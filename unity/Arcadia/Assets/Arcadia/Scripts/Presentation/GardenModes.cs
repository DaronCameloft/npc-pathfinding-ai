using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Arcadia.Navigation;

namespace Arcadia
{
    public enum GardenMode { Navigation, Corridor, Patrol, Loot }

    public sealed partial class GardenModes : MonoBehaviour
    {
        public GardenMode Mode { get; private set; }
        public AlgorithmInfo Info { get; private set; }
        public string Status { get; private set; }
        public bool Ready { get; private set; }
        public bool Failed { get; private set; }
        public int Seed { get; private set; } = 2026;
        public int Capacity { get; private set; } = 20;
        public AnalisisPasillo Corridor { get; private set; }
        public RedPatrullaje Patrol { get; private set; }
        public SeleccionBotin Loot { get; private set; }
        public bool Closed { get; private set; }
        public bool Walking { get; private set; }
        public int VisibleRows { get; private set; }
        public int Reconstructed { get; private set; }
        public Transform Scene { get; private set; }
        ArcadiaGame game;
        RequestCancellation token;
        AlgorithmInfo[] catalog;
        GridCell[] cut = Array.Empty<GridCell>();
        bool wasPaused, wasClose, wasFoggy, chestOpen;
        Material veil;
        Vector3 oldFocus;
        Transform oldFollow;
        float oldDistance, oldYaw, oldPitch, oldLimit;
        readonly Dictionary<Color, Material> materials = new Dictionary<Color, Material>();
        readonly List<TextMesh> labels = new List<TextMesh>();
        static readonly Color Mint=new Color(.15f,.94f,.68f), Amber=new Color(1,.66f,.15f), Red=new Color(.95f,.15f,.19f);
        static readonly Color[] LaneColors={new Color(.12f,.92f,.78f),new Color(1,.65f,.12f),new Color(.7f,.4f,1)};
        internal void Initialize(ArcadiaGame owner) { game=owner; }

        public void Select(GardenMode mode)
        {
            if (mode==Mode) return;
            if (Mode==GardenMode.Navigation)
            {
                var rig=game.Rig;
                wasFoggy=RenderSettings.fog;
                wasPaused=game.Navigator.IsPaused;
                oldFocus=rig.Focus; oldFollow=rig.Follow; oldDistance=rig.Distance; oldPitch=rig.Pitch; oldYaw=rig.Yaw;
                wasClose=rig.CloseView; oldLimit=rig.MaxTacticalDistance;
                game.Navigator.SetPaused(true);
                game.ShowNavigation(false);
            }
            CancelScene();
            Mode=mode;
            RenderSettings.fog=wasFoggy && (mode==GardenMode.Navigation || mode==GardenMode.Loot);
            if (mode==GardenMode.Navigation)
            {
                var rig=game.Rig;
                rig.Focus=oldFocus; rig.Follow=oldFollow; rig.Distance=oldDistance; rig.Pitch=oldPitch; rig.Yaw=oldYaw;
                rig.CloseView=wasClose; rig.MaxTacticalDistance=oldLimit; rig.Snap();
                game.ShowNavigation(true);
                game.Navigator.SetPaused(wasPaused);
                return;
            }
            Closed=false; chestOpen=false; cut=Array.Empty<GridCell>();
            Reload();
        }

        void CancelScene()
        {
            token?.Cancel(); StopAllCoroutines();
            if(Scene) { Scene.gameObject.SetActive(false); Destroy(Scene.gameObject); }
            Scene=null; Corridor=null; Patrol=null; Loot=null; Info=null;
            Ready=false; Failed=false; Walking=false; VisibleRows=0; Reconstructed=0; labels.Clear();
        }

        public void Reload()
        {
            if(Mode==GardenMode.Navigation)return;
            CancelScene();
            Scene=new GameObject("Experimento " + Mode).transform;
            Scene.SetParent(transform,false);
            token=new RequestCancellation();
            StartCoroutine(Load());
        }

        IEnumerator Load()
        {
            Status="Consultando el motor…";
            if(catalog==null) yield return game.Client.GetCatalog(value=>catalog=value, Fail, token);
            if(Failed)yield break;
            string key=Mode==GardenMode.Corridor?"edmonds_karp":Mode==GardenMode.Patrol?"kruskal":"mochila";
            Info=Array.Find(catalog, a=>a.clave==key);
            if(Info==null){Fail("El algoritmo no figura en el catálogo del motor.");yield break;}
            switch(Mode)
            {
                case GardenMode.Corridor:
                    yield return game.Client.Corridor(game.Map.Name,Closed?cut:Array.Empty<GridCell>(),r=>Corridor=r,Fail,token);
                    if(!Failed)yield return ShowCorridor();
                    break;
                case GardenMode.Patrol:
                    yield return game.Client.Patrol(game.Map.Name,Seed,r=>Patrol=r,Fail,token);
                    if(!Failed)yield return ShowPatrol();
                    break;
                case GardenMode.Loot:
                    PrepareChest();
                    if(!chestOpen){Status="Abre el cofre para examinar el botín.";Ready=true;yield break;}
                    yield return game.Client.Loot(Capacity,r=>Loot=r,Fail,token);
                    if(!Failed)yield return ShowLoot();
                    break;
            }
        }

        void Fail(string message){Failed=true;Status=message;}
        public void ToggleCut(){if(Mode!=GardenMode.Corridor || !Ready)return;Closed=!Closed;Reload();}
        public void OtherPoints(){if(Mode!=GardenMode.Patrol)return;Seed++;Reload();}
        public void OpenChest(){if(Mode!=GardenMode.Loot)return;chestOpen=true;Reload();}
        public void SetCapacity(int value)
        {
            value=Mathf.Clamp(value,1,60);
            if(Mode!=GardenMode.Loot || Capacity==value)return;
            Capacity=value; OpenChest();
        }
        void Frame(Vector3 focus,float distance,float pitch=76)
        {
            var rig=game.Rig;
            rig.Follow=null; rig.CloseView=false; rig.MaxTacticalDistance=320;
            rig.Focus=focus; rig.Distance=distance; rig.Pitch=pitch; rig.Yaw=180; rig.Snap();
        }
        Material Paint(Color color)
        {
            if(!materials.TryGetValue(color,out var material))
                materials[color]=material=game.World.Material("Jardín",color,0,.35f,.25f);
            return material;
        }
        GameObject Shape(string name,PrimitiveType type,Vector3 position,Vector3 scale,Color color,bool solid=false)
        {
            var obj=GameObject.CreatePrimitive(type);
            obj.name=name;obj.transform.SetParent(Scene,false);obj.transform.position=position;obj.transform.localScale=scale;
            obj.GetComponent<Renderer>().sharedMaterial=Paint(color);
            obj.GetComponent<Collider>().enabled=solid;
            return obj;
        }
        LineRenderer Line(string name,IEnumerable<Vector3> points,Color color,float width)
        {
            var line=new GameObject(name).AddComponent<LineRenderer>();
            line.transform.SetParent(Scene,false);line.sharedMaterial=Paint(color);line.widthMultiplier=width;
            var vertices=points.ToArray();line.positionCount=vertices.Length;line.SetPositions(vertices);
            return line;
        }
        Transform Guardian(string name,Vector3 position,Color color,float scale)
        {
            var root=new GameObject(name).transform;root.SetParent(Scene,false);root.position=position;
            var model=Instantiate(game.Navigator.VisualRoot.gameObject,root);model.SetActive(true);
            model.transform.localPosition=Vector3.zero;model.transform.localRotation=Quaternion.identity;
            model.transform.localScale=Vector3.one*scale;
            foreach(var ring in model.GetComponentsInChildren<LineRenderer>()){ring.sharedMaterial=Paint(color);ring.widthMultiplier=.1f;}
            return root;
        }
        void Caption(Transform parent,string text,float size,float height)
        {
            var label=new GameObject(text).AddComponent<TextMesh>();label.transform.SetParent(parent,true);
            label.transform.position=parent.position+Vector3.up*height;label.text=text;label.anchor=TextAnchor.MiddleCenter;
            label.fontSize=48;label.characterSize=size;label.color=Color.white;labels.Add(label);
        }
        void LateUpdate()
        {
            foreach(var label in labels)if(label)label.transform.rotation=game.Rig.transform.rotation;
        }
        void OnDestroy(){token?.Cancel();if(veil)Destroy(veil);if(Mode!=GardenMode.Navigation)RenderSettings.fog=wasFoggy;}
    }
}
