using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using Arcadia.Navigation;

namespace Arcadia
{
    // Decorative geometry never changes the grid. Every walkable tile stays at y=0.
    public sealed class ArcadiaWorld : MonoBehaviour
    {
        public GameObject ArchModel, ColumnModel, FernModel, RockModel;
        public Material LitTemplate;
        public MapData Map { get; private set; }
        public readonly Dictionary<GridCell, GameObject> Obstacles = new Dictionary<GridCell, GameObject>();
        readonly List<Material> ownedMaterials = new List<Material>();
        readonly List<Mesh> ownedMeshes = new List<Mesh>();
        Material ivory, ceramic, bronze, teal, bark, green, darkGreen, flower, water;
        System.Random random;
        Transform detailRoot, obstacleRoot;
        float[,] terrainTop;
        Renderer[] cameraDecor;
        readonly HashSet<Renderer> hiddenDecor=new HashSet<Renderer>();

        public Material Material(string name, Color color, float metal = 0, float smooth = .2f, float emission = 0)
        {
            var m = LitTemplate != null ? new Material(LitTemplate) : new Material(Shader.Find("Universal Render Pipeline/Lit"));
            m.name = name; m.SetColor("_BaseColor", color); m.color = color;
            m.SetFloat("_Metallic", metal); m.SetFloat("_Smoothness", smooth);
            if (emission > 0) { m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", color * emission); }
            ownedMaterials.Add(m); return m;
        }

        public void Build(MapData map)
        {
            Map = map; random = new System.Random(184);terrainTop=new float[map.Height,map.Width];
            ivory = Material("Caliza antigua", new Color(.63f,.61f,.43f));
            ceramic = Material("Ceramica de Auri", new Color(.84f,.88f,.81f), .12f, .4f);
            bronze = Material("Bronce envejecido", new Color(.39f,.24f,.095f), .7f, .33f);
            teal = Material("Cristal de Arcadia", new Color(.12f,.83f,.65f), .25f,.65f,1.8f);
            bark = Material("Cedro", new Color(.18f,.15f,.09f));
            green = Material("Hojas iluminadas", new Color(.25f,.43f,.16f));
            darkGreen = Material("Hojas de sombra", new Color(.075f,.22f,.12f));
            flower = Material("Flores silvestres", new Color(.67f,.44f,.57f));
            water = Material("Obsidiana azul", new Color(.055f,.20f,.20f),.65f,.85f);
            detailRoot = new GameObject("Jardin y arquitectura").transform; detailRoot.SetParent(transform, false);
            obstacleRoot = new GameObject("Obstaculos comunicados al motor").transform; obstacleRoot.SetParent(transform, false);
            var groundMats = new Material[6];
            var walls = new Material[4];
            for(int i=0;i<6;i++) groundMats[i]=Material("Losas "+i, Color.Lerp(new Color(.47f,.52f,.43f),new Color(.57f,.59f,.48f),i/5f));
            for(int i=0;i<4;i++) walls[i]=Material("Muros "+i, Color.Lerp(new Color(.43f,.50f,.41f),new Color(.63f,.67f,.54f),i/3f));
            // Chunked combined geometry: no GameObject per cell, no collider per tile.
            const int chunk=24;
            for(int rz=0;rz<map.Height;rz+=chunk) for(int cx=0;cx<map.Width;cx+=chunk)
            {
                var floors=new MeshDraft[6]; var rocks=new MeshDraft[4];
                for(int i=0;i<6;i++)floors[i]=new MeshDraft();
                for(int i=0;i<4;i++)rocks[i]=new MeshDraft();
                for(int row=rz;row<Math.Min(rz+chunk,map.Height);row++) for(int col=cx;col<Math.Min(cx+chunk,map.Width);col++)
                {
                    var p=new GridCell(row,col); bool walk=map.IsWalkable(p);
                    if(walk)
                    {
                        int shade=random.Next(6);
                        floors[shade].Box(new Vector3(col,-.11f,row),new Vector3(.992f,.22f,.992f));
                        // Flush tesserae on the showcase floor, never physical obstacles.
                        if(InShowcase(p)&&random.NextDouble()<.025)
                            floors[(shade+2)%6].Box(new Vector3(col,.003f,row),new Vector3(.3f,.006f,.3f));
                    }
                    else if(NearWalkable(p,2))
                    {
                        bool edge=NearWalkable(p,1); float h=edge?1.15f+(float)random.NextDouble()*.62f:2.2f+(float)random.NextDouble()*1.1f;
                        terrainTop[row,col]=h-.04f;
                        int shade=random.Next(4);
                        rocks[shade].Box(new Vector3(col,h*.5f-.12f,row),new Vector3(.985f,h,.985f));
                        if(edge) rocks[(shade+1)%4].Box(new Vector3(col,h-.10f,row),new Vector3(1.01f,.12f,1.01f));
                    }
                }
                var group=new GameObject("Sector "+rz+"-"+cx).transform;group.SetParent(transform,false);
                for(int i=0;i<6;i++)Attach(floors[i],groundMats[i],group,"Suelo");
                for(int i=0;i<4;i++)Attach(rocks[i],walls[i],group,"Piedra");
            }
            // A dark mineral bed under the actual navigable geometry gives the ruins depth.
            Primitive(PrimitiveType.Cube,"Basamento",new Vector3(map.Width*.5f,-1.2f,map.Height*.5f),new Vector3(map.Width+4,1.8f,map.Height+4),water,transform);
            Decorate();
            BuildGateFrame();
            BuildLandmarks();
            cameraDecor=detailRoot.GetComponentsInChildren<Renderer>();
        }

        bool InShowcase(GridCell p)=>p.Row>=78&&p.Row<=118&&p.Column>=82&&p.Column<=134;
        bool NearWalkable(GridCell p,int radius)
        {
            for(int r=-radius;r<=radius;r++)for(int c=-radius;c<=radius;c++)
                if(Map.IsWalkable(new GridCell(p.Row+r,p.Column+c)))return true;
            return false;
        }

        void Decorate()
        {
            for(int r=77;r<=119;r++)for(int c=81;c<=135;c++)
            {
                var cell=new GridCell(r,c);if(Map.IsWalkable(cell)||!NearWalkable(cell,1))continue;
                float top=terrainTop[r,c];
                double roll=random.NextDouble();
                if(roll<.09) Tree(new Vector3(c,top,r),.65f+(float)random.NextDouble()*.6f);
                else if(roll<.21) Plant(new Vector3(c,top,r),.5f+(float)random.NextDouble()*.6f);
                else if(roll<.255) RuinPillar(new Vector3(c,top,r),.8f+(float)random.NextDouble()*.5f);
                else if(roll<.30&&RockModel!=null){var rock=SpawnModel(RockModel,new Vector3(c,top,r),Quaternion.Euler(0,random.Next(360),0));rock.transform.localScale=Vector3.one*.65f;}
                if(random.NextDouble()<.22)
                    Primitive(PrimitiveType.Sphere,"Musgo sobre piedra",new Vector3(c,top,r),new Vector3(.92f,.16f,.92f),darkGreen,detailRoot);
                if(roll>.80)
                    for(int k=0;k<3;k++)
                    {
                        Vector3 p=new Vector3(c+(k-1)*.20f,top+.13f,r+.18f);
                        Primitive(PrimitiveType.Cylinder,"Tallo",p,new Vector3(.025f,.13f,.025f),darkGreen,detailRoot);
                        Primitive(PrimitiveType.Sphere,"Flor de las ruinas",p+Vector3.up*.13f,new Vector3(.20f,.08f,.20f),flower,detailRoot);
                    }
            }
            // Landmarks sit on static non-traversable islands only.
            foreach(var p in new[]{new GridCell(98,107),new GridCell(99,107),new GridCell(96,107),new GridCell(100,106)})
                if(!Map.IsWalkable(p)){Beacon(p.ToWorld(2.4f),1.2f);break;}
            // Fine grasses along the edge of a tile; their footprint stays visually peripheral.
            for(int r=80;r<116;r++)for(int c=84;c<133;c++)
            {
                var p=new GridCell(r,c);if(!Map.IsWalkable(p)||random.NextDouble()>.12)continue;
                int dr=random.Next(2)*2-1;
                if(!Map.IsWalkable(new GridCell(r+dr,c))) Plant(new Vector3(c+.32f,.01f,r+dr*.36f),.27f);
            }
            AmbientMotes(new Vector3(108,1.2f,99));
        }

        void Tree(Vector3 p,float scale)
        {
            var root=new GameObject("Cedro del santuario").transform;root.SetParent(detailRoot,false);root.position=p;
            Primitive(PrimitiveType.Cylinder,"Tronco",new Vector3(0,1.25f,0),new Vector3(.22f,1.3f,.24f)*scale,bark,root,true);
            for(int i=0;i<4;i++)
            {
                float a=i*2.4f;
                Vector3 o=new Vector3(Mathf.Cos(a)*.7f,2.3f+(i%2)*.6f,Mathf.Sin(a)*.6f)*scale;
                var crown=Primitive(PrimitiveType.Sphere,"Copa",o,new Vector3(1.8f,.85f,1.65f)*scale,i%2==0?green:darkGreen,root,true);
                crown.transform.localRotation=Quaternion.Euler(0,i*37,12);
            }
        }

        void Plant(Vector3 p,float scale)
        {
            if(FernModel!=null)
            {
                var fern=SpawnModel(FernModel,p,Quaternion.Euler(0,random.Next(360),0));
                fern.transform.localScale=Vector3.one*scale;return;
            }
            for(int i=0;i<5;i++)
            {
                float a=i*Mathf.PI*.4f;
                var leaf=Primitive(PrimitiveType.Sphere,"Helecho",p+new Vector3(Mathf.Cos(a)*.2f,.2f,Mathf.Sin(a)*.2f)*scale,new Vector3(.15f,.7f,.26f)*scale,i%2==0?green:darkGreen,detailRoot);
                leaf.transform.rotation=Quaternion.Euler(Mathf.Sin(a)*45,i*72,Mathf.Cos(a)*45);
            }
        }

        void RuinPillar(Vector3 p,float scale)
        {
            if(ColumnModel!=null){var o=SpawnModel(ColumnModel,p,Quaternion.Euler(0,random.Next(360),0));o.transform.localScale=Vector3.one*scale;return;}
            Primitive(PrimitiveType.Cylinder,"Columna",p+Vector3.up*scale,new Vector3(.62f,scale,.62f),ivory,detailRoot);
            Primitive(PrimitiveType.Cube,"Capitel",p+Vector3.up*2*scale,new Vector3(.9f,.22f,.9f),ivory,detailRoot);
        }

        public void Beacon(Vector3 p,float scale)
        {
            var o=Primitive(PrimitiveType.Cylinder,"Pedestal del guardian",p,new Vector3(1.1f,.35f,1.1f)*scale,bronze,detailRoot);
            var crystal=Primitive(PrimitiveType.Cube,"Corazon de Arcadia",p+Vector3.up*.85f*scale,new Vector3(.4f,.85f,.4f)*scale,teal,detailRoot);
            crystal.transform.rotation=Quaternion.Euler(0,45,25);
            var light=crystal.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(.25f,1,.78f);light.intensity=1.6f;light.range=4;
        }

        void BuildGateFrame()
        {
            for(int r=86;r<=95;r+=9)
            {
                Primitive(PrimitiveType.Cube,"Jamba de la compuerta",new Vector3(99,.85f,r),new Vector3(.65f,1.7f,.55f),bronze,detailRoot);
                Primitive(PrimitiveType.Sphere,"Sello de energia",new Vector3(99,1.9f,r),Vector3.one*.24f,teal,detailRoot);
            }
            // Inlaid rails, flush with the floor; raised panels are the actual blockers.
            Primitive(PrimitiveType.Cube,"Guia de bronce",new Vector3(99,.012f,90.5f),new Vector3(.16f,.024f,9),bronze,detailRoot);
        }

        void BuildLandmarks()
        {
            // Supports lie on blocked cells; the central opening preserves the two-cell corridor.
            if(ArchModel!=null)
            {
                var arch=SpawnModel(ArchModel,new Vector3(102,0,88.5f),Quaternion.Euler(0,90,0));
                arch.name="Portal del pasadizo";arch.transform.localScale=Vector3.one*1.05f;
            }
            foreach(var cell in new[]{new GridCell(106,123),new GridCell(107,92)})
            {
                var plate=Primitive(PrimitiveType.Cylinder,"Medallon del guardian",cell.ToWorld(.012f),new Vector3(1.45f,.012f,1.45f),bronze,detailRoot);
                for(int i=0;i<12;i++)
                {
                    float a=i*Mathf.PI/6;
                    var glyph=Primitive(PrimitiveType.Cube,"Mosaico de orientacion",cell.ToWorld(.028f)+new Vector3(Mathf.Cos(a)*.57f,0,Mathf.Sin(a)*.57f),new Vector3(.04f,.012f,.13f),ivory,detailRoot);
                    glyph.transform.rotation=Quaternion.Euler(0,-i*30,0);
                }
            }
            // A lantern beside the starting plaza makes the first view readable.
            var lampCell=new GridCell(110,122);
            if(!Map.IsWalkable(lampCell))
            {
                var p=lampCell.ToWorld(1.6f);
                RuinPillar(p,.9f);Beacon(p+Vector3.up*1.9f,.6f);
            }
        }

        public void SyncObstacles(IEnumerable<GridCell> blocked)
        {
            var wanted=new HashSet<GridCell>(blocked);
            var remove=new List<GridCell>();
            foreach(var pair in Obstacles)if(!wanted.Contains(pair.Key)){Destroy(pair.Value);remove.Add(pair.Key);}
            foreach(var cell in remove)Obstacles.Remove(cell);
            foreach(var cell in wanted)
            {
                if(Obstacles.ContainsKey(cell))continue;
                var root=new GameObject("Barrera "+cell);root.transform.SetParent(obstacleRoot,false);root.transform.position=cell.ToWorld();
                Primitive(PrimitiveType.Cube,"Panel",new Vector3(0,.64f,0),new Vector3(.78f,1.28f,.78f),bronze,root.transform,true);
                Primitive(PrimitiveType.Cube,"Sello",new Vector3(0,1.3f,0),new Vector3(.81f,.06f,.81f),teal,root.transform,true);
                Primitive(PrimitiveType.Cube,"Madera",new Vector3(0,.65f,.405f),new Vector3(.53f,.85f,.03f),bark,root.transform,true);
                Obstacles.Add(cell,root);
            }
        }

        public void RemapModel(GameObject model)
        {
            foreach(var r in model.GetComponentsInChildren<Renderer>())
            {
                var mats=r.sharedMaterials;
                for(int i=0;i<mats.Length;i++)
                {
                    string n=mats[i]!=null?mats[i].name.ToLowerInvariant():"";
                    mats[i]=n.Contains("ceramic")?ceramic:n.Contains("leaf")?green:n.Contains("light")||n.Contains("cyan")?teal:n.Contains("brass")?bronze:n.Contains("moss")?darkGreen:n.Contains("joint")||n.Contains("visor")?water:ivory;
                }
                r.sharedMaterials=mats;
            }
        }

        GameObject SpawnModel(GameObject prefab,Vector3 position,Quaternion yaw)
        {
            var obj=Instantiate(prefab,position,yaw*prefab.transform.localRotation,detailRoot);
            RemapModel(obj);return obj;
        }

        // Keep the sight line above solid grid geometry. This never changes navigation.
        public Vector3 ClearCameraSight(Vector3 focus,Vector3 candidate)
        {
            if(Map==null)return candidate;
            float requiredY=candidate.y;
            int samples=Mathf.Max(16,Mathf.CeilToInt(Vector3.Distance(focus,candidate)*5));
            for(int i=1;i<=samples;i++)
            {
                float t=i/(float)samples;Vector3 p=Vector3.Lerp(focus,candidate,t);
                var cell=GridCell.FromWorld(p);
                if(cell.Row<0||cell.Row>=Map.Height||cell.Column<0||cell.Column>=Map.Width||Map.IsWalkable(cell))continue;
                float top=terrainTop[cell.Row,cell.Column]+.3f;
                requiredY=Mathf.Max(requiredY,focus.y+(top-focus.y)/t);
            }
            candidate.y=requiredY;return candidate;
        }

        // Botanical cutaway: hide only decoration crossing the view of the followed actor.
        public void UpdateCameraOcclusion(Vector3 eye,Vector3 target,bool following)
        {
            if(cameraDecor==null)return;
            Vector3 delta=target-eye;float length=delta.magnitude;
            Ray sight=new Ray(eye,delta.normalized);
            foreach(var renderer in cameraDecor)
            {
                if(renderer==null||renderer is ParticleSystemRenderer)continue;
                Bounds bounds=renderer.bounds;bounds.Expand(.22f);
                bool hide=following&&bounds.IntersectRay(sight,out float hit)&&hit<length-.25f;
                if(hide){if(hiddenDecor.Add(renderer))renderer.shadowCastingMode=ShadowCastingMode.ShadowsOnly;}
                else if(hiddenDecor.Remove(renderer))renderer.shadowCastingMode=ShadowCastingMode.On;
            }
        }

        void AmbientMotes(Vector3 p)
        {
            var obj=new GameObject("Polen en la luz");obj.transform.SetParent(detailRoot,false);obj.transform.position=p;
            var ps=obj.AddComponent<ParticleSystem>();var main=ps.main;main.loop=true;main.startLifetime=12;main.startSpeed=.1f;main.startSize=.035f;main.maxParticles=100;main.startColor=new Color(.9f,.82f,.46f,.5f);main.simulationSpace=ParticleSystemSimulationSpace.World;
            var emission=ps.emission;emission.rateOverTime=6;
            var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Box;shape.scale=new Vector3(35,3,28);
            var rend=obj.GetComponent<ParticleSystemRenderer>();rend.sharedMaterial=teal;
        }

        void Attach(MeshDraft draft,Material mat,Transform parent,string name)
        {
            if(draft.Vertices.Count==0)return;
            var obj=new GameObject(name);obj.transform.SetParent(parent,false);
            Mesh mesh=draft.Create();ownedMeshes.Add(mesh);obj.AddComponent<MeshFilter>().sharedMesh=mesh;
            var renderer=obj.AddComponent<MeshRenderer>();renderer.sharedMaterial=mat;renderer.shadowCastingMode=ShadowCastingMode.On;
        }

        public static GameObject Primitive(PrimitiveType type,string name,Vector3 position,Vector3 scale,Material material,Transform parent,bool local=false)
        {
            var o=GameObject.CreatePrimitive(type);o.name=name;o.transform.SetParent(parent,false);
            if(local)o.transform.localPosition=position;else o.transform.position=position;
            o.transform.localScale=scale;o.GetComponent<Renderer>().sharedMaterial=material;
            var collider=o.GetComponent<Collider>();if(collider!=null)Destroy(collider);
            return o;
        }

        void OnDestroy(){foreach(var m in ownedMaterials)if(m!=null)Destroy(m);foreach(var m in ownedMeshes)if(m!=null)Destroy(m);}
    }

    internal sealed class MeshDraft
    {
        public readonly List<Vector3> Vertices=new List<Vector3>();
        readonly List<Vector3> normals=new List<Vector3>();
        readonly List<Vector2> uv=new List<Vector2>();
        readonly List<int> triangles=new List<int>();
        void Quad(Vector3 a,Vector3 b,Vector3 c,Vector3 d,Vector3 normal)
        {
            int s=Vertices.Count;Vertices.AddRange(new[]{a,b,c,d});normals.AddRange(new[]{normal,normal,normal,normal});
            uv.AddRange(new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up});triangles.AddRange(new[]{s,s+1,s+2,s,s+2,s+3});
        }
        public void Box(Vector3 c,Vector3 size)
        {
            Vector3 p=c-size*.5f,q=c+size*.5f;
            Quad(new Vector3(p.x,q.y,p.z),new Vector3(p.x,q.y,q.z),new Vector3(q.x,q.y,q.z),new Vector3(q.x,q.y,p.z),Vector3.up);
            Quad(new Vector3(p.x,p.y,p.z),new Vector3(q.x,p.y,p.z),new Vector3(q.x,p.y,q.z),new Vector3(p.x,p.y,q.z),Vector3.down);
            Quad(new Vector3(p.x,p.y,q.z),new Vector3(q.x,p.y,q.z),new Vector3(q.x,q.y,q.z),new Vector3(p.x,q.y,q.z),Vector3.forward);
            Quad(new Vector3(q.x,p.y,p.z),new Vector3(p.x,p.y,p.z),new Vector3(p.x,q.y,p.z),new Vector3(q.x,q.y,p.z),Vector3.back);
            Quad(new Vector3(q.x,p.y,q.z),new Vector3(q.x,p.y,p.z),new Vector3(q.x,q.y,p.z),new Vector3(q.x,q.y,q.z),Vector3.right);
            Quad(new Vector3(p.x,p.y,p.z),new Vector3(p.x,p.y,q.z),new Vector3(p.x,q.y,q.z),new Vector3(p.x,q.y,p.z),Vector3.left);
        }
        public Mesh Create(){var m=new Mesh{name="Arcadia combined geometry",indexFormat=IndexFormat.UInt32};m.SetVertices(Vertices);m.SetNormals(normals);m.SetUVs(0,uv);m.SetTriangles(triangles,0);m.RecalculateBounds();return m;}
    }
}
