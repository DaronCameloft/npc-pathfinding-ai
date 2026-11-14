using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.EventSystems;
using Arcadia.Navigation;

namespace Arcadia
{
    public sealed class ArcadiaGame : MonoBehaviour
    {
        public GameObject AuriModel;
        public GameObject FocaWatonaModel;
        public Material FocaSkin,FocaCream,FocaEyes,FocaNose,FocaWhiskers,FocaEyelids;
        public CharacterKind NpcCharacter {get;private set;}
        public CharacterKind PlayerCharacter {get;private set;}
        public string NpcCharacterName=>CharacterName(NpcCharacter);
        public string PlayerCharacterName=>CharacterName(PlayerCharacter);
        public Transform PlayerRoot=>explorer;
        public ArcadiaWorld World;
        public ArcadiaCamera Rig;
        public string ApiUrl="http://127.0.0.1:8000";
        public NpcNavigator Navigator {get;private set;}
        public EngineClient Client {get;private set;}
        public MapData Map {get;private set;}
        public bool Online {get;private set;}
        public bool GateClosed {get;private set;}
        public bool Sealed {get;private set;}
        public bool ExploreMode {get;private set;}
        public bool Following {get;private set;}
        public bool ShowRoute=true;
        public bool ShowExploration;
        public string Message {get;private set;}="Conectando con el motor...";
        public string Connection {get;private set;}="CONECTANDO";
        public readonly GridCell StartCell=new GridCell(106,123),GoalCell=new GridCell(107,92);
        public event Action Changed;
        readonly HashSet<GridCell> manual=new HashSet<GridCell>();
        readonly List<GridCell> gate=new List<GridCell>();
        readonly List<GridCell> seal=new List<GridCell>{new GridCell(88,102),new GridCell(89,102)};
        Transform explorer,marker;
        LineRenderer path;
        GameObject traceObject;
        float followAt;
        bool connecting;
        int reconnectGeneration;
        ArcadiaHud hud;
        Material routeMat,markerMat;
        Material explorerAmber,npcRole;
        const string NpcPreference="Arcadia.Character.Npc",PlayerPreference="Arcadia.Character.Player";

        IEnumerator Start()
        {
            Application.targetFrameRate=60;
            for(int row=87;row<=94;row++)gate.Add(new GridCell(row,99));
            Client=gameObject.AddComponent<EngineClient>();Client.BaseUrl=ApiUrl;Client.RequestTimeoutSeconds=6;
            try
            {
                Map=EngineClient.ParseMap(File.ReadAllText(Path.Combine(Application.streamingAssetsPath,"Arcadia/den011d.json")));
                World.Build(Map);CreateActors();
                Rig.World=World;
                Rig.Follow=Navigator.transform;Rig.CloseView=true;Rig.Focus=StartCell.ToWorld(.5f);Rig.Distance=7;Rig.Pitch=36;Rig.Yaw=25;Rig.Snap();
                UpdateCharacterCamera();
                hud=gameObject.AddComponent<ArcadiaHud>();hud.Initialize(this);
            }
            catch(Exception e){Debug.LogException(e);yield break;}
            yield return Connect();
        }

        public void Reconnect(){if(!connecting)StartCoroutine(Connect());}
        IEnumerator Connect()
        {
            connecting=true;int generation=++reconnectGeneration;Connection="CONECTANDO";Changed?.Invoke();
            yield return Client.GetMap("den011d",live=>
            {
                if(generation!=reconnectGeneration)return;
                bool same=live.Width==Map.Width&&live.Height==Map.Height;
                if(same)for(int i=0;i<Map.Height;i++)if(live.Rows[i]!=Map.Rows[i]){same=false;break;}
                if(!same){Online=false;Connection="MAPA DISTINTO";Notify("El mapa del motor no coincide con el terreno. Reinicia con el dataset original.");return;}
                Online=true;Connection="MOTOR CONECTADO";Notify(NpcCharacterName+" está listo. Inicia el recorrido o elige un destino sobre el suelo.");
            },error=>{Online=false;Connection="SIN CONEXION";Notify("Activa el motor local y pulsa Reconectar. El terreno está disponible; las rutas requieren Python.");Debug.LogWarning(error);});
            connecting=false;Changed?.Invoke();
        }

        void CreateActors()
        {
            var root=new GameObject("Auri - agente del motor");root.transform.position=StartCell.ToWorld();
            NpcCharacter=ReadCharacter(NpcPreference);PlayerCharacter=ReadCharacter(PlayerPreference);
            Transform visual=CreateCharacter(root.transform,false,NpcCharacter);
            Navigator=root.AddComponent<NpcNavigator>();Navigator.Initialize(Client,Map,StartCell,visual);Navigator.Speed=2.6f;
            Navigator.RouteChanged+=OnRoute;Navigator.RouteInvalidated+=()=>{if(path)path.positionCount=0;ClearTrace();};
            Navigator.StateChanged+=_=>Changed?.Invoke();Navigator.Error+=e=>{Following=false;Online=false;Connection="ERROR DEL MOTOR";Notify(e);};
            Navigator.Arrived+=()=>{Notify("Destino alcanzado. "+NpcCharacterName+" espera tu próxima orden.");};
            var player=new GameObject("Explorador - control directo");explorer=player.transform;explorer.position=new GridCell(107,123).ToWorld();CreateCharacter(explorer,true,PlayerCharacter);explorer.gameObject.SetActive(false);
            routeMat=World.Material("Ruta turquesa",new Color(.18f,.89f,.73f),0,.5f,1.1f);
            markerMat=World.Material("Destino dorado",new Color(1,.68f,.22f),.4f,.5f,1.3f);
            var line=new GameObject("Ruta calculada por Python");path=line.AddComponent<LineRenderer>();path.sharedMaterial=routeMat;path.widthMultiplier=.075f;path.numCornerVertices=3;path.numCapVertices=3;path.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
            marker=new GameObject("Destino").transform;
            var ring=marker.gameObject.AddComponent<LineRenderer>();ring.sharedMaterial=markerMat;ring.widthMultiplier=.07f;ring.loop=true;ring.positionCount=48;ring.useWorldSpace=false;
            for(int i=0;i<48;i++){float a=i*Mathf.PI/24;ring.SetPosition(i,new Vector3(Mathf.Cos(a)*.52f,.07f,Mathf.Sin(a)*.52f));}
            marker.position=GoalCell.ToWorld();
            var light=marker.gameObject.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.7f,.25f);light.intensity=.8f;light.range=3;
        }

        public static string CharacterName(CharacterKind kind)=>kind==CharacterKind.FocaWatona?"Foca Watona":"Auri";
        CharacterKind ReadCharacter(string key)
        {
            var kind=(CharacterKind)PlayerPrefs.GetInt(key,0);
            return kind==CharacterKind.FocaWatona&&FocaWatonaModel!=null?kind:CharacterKind.Auri;
        }
        public void SetNpcCharacter(CharacterKind kind)=>SetCharacter(kind,false);
        public void SetPlayerCharacter(CharacterKind kind)=>SetCharacter(kind,true);
        void SetCharacter(CharacterKind kind,bool player)
        {
            if(Navigator==null||explorer==null)return;
            if(kind!=CharacterKind.Auri&&kind!=CharacterKind.FocaWatona)return;
            if(kind==CharacterKind.FocaWatona&&FocaWatonaModel==null){Notify("El modelo Foca Watona no está disponible en esta escena. Actualiza la escena desde Arcadia.");return;}
            if(kind==(player?PlayerCharacter:NpcCharacter))return;
            // Keep the stable facing wrapper: no reset, request cancellation or path changes.
            Transform facing=player?explorer.GetChild(0):Navigator.VisualRoot;
            ReplaceCharacterModel(facing,player,kind);
            if(player)PlayerCharacter=kind;else NpcCharacter=kind;
            UpdateCharacterCamera();
            PlayerPrefs.SetInt(player?PlayerPreference:NpcPreference,(int)kind);PlayerPrefs.Save();
            Notify((player?"Tu personaje: ":"Compañero: ")+CharacterName(kind)+".");
        }
        Transform CreateCharacter(Transform parent,bool player,CharacterKind kind)
        {
            // Navigation rotates this Unity-aligned wrapper, preserving the FBX axis conversion.
            var facing=new GameObject("Orientacion del guardian").transform;facing.SetParent(parent,false);
            ReplaceCharacterModel(facing,player,kind);
            return facing;
        }
        void ReplaceCharacterModel(Transform facing,bool player,CharacterKind kind)
        {
            foreach(Transform child in facing){child.gameObject.SetActive(false);Destroy(child.gameObject);}
            bool sealModel=kind==CharacterKind.FocaWatona;
            var prefab=sealModel?FocaWatonaModel:AuriModel;
            GameObject model;
            if(prefab!=null){model=Instantiate(prefab,facing);model.name=CharacterName(kind)+(player?" - jugador":" - NPC");model.transform.localPosition=Vector3.zero;if(sealModel)RemapSeal(model);else World.RemapModel(model);}
            else model=ArcadiaWorld.Primitive(PrimitiveType.Capsule,"Auri provisional",new Vector3(0,.5f,0),new Vector3(.5f,.5f,.5f),World.Material("Ceramica",Color.white),facing,true);
            model.transform.localScale=Vector3.one*(sealModel?.85f:player?1.15f:1.35f);
            if(sealModel)model.AddComponent<SealMotion>();else model.AddComponent<AuriMotion>();
            if(player&&!sealModel)
            {
                if(explorerAmber==null)explorerAmber=World.Material("Explorador ambar",new Color(1,.58f,.12f),.2f,.4f,1.5f);
                foreach(var renderer in model.GetComponentsInChildren<Renderer>())
                {
                    var mats=renderer.sharedMaterials;for(int i=0;i<mats.Length;i++)if(mats[i].name.Contains("Cristal"))mats[i]=explorerAmber;renderer.sharedMaterials=mats;
                }
            }
            // A small role ring distinguishes identical choices without recoloring the reference skin.
            var ring=new GameObject(player?"Rol jugador - ambar":"Rol NPC - turquesa").AddComponent<LineRenderer>();
            ring.transform.SetParent(facing,false);ring.useWorldSpace=false;ring.loop=true;ring.widthMultiplier=.022f;ring.positionCount=48;
            if(player&&explorerAmber==null)explorerAmber=World.Material("Explorador ambar",new Color(1,.58f,.12f),.2f,.4f,1.5f);
            if(!player&&npcRole==null)npcRole=World.Material("Rol compañero",new Color(.18f,.89f,.73f),0,.4f,.6f);
            ring.sharedMaterial=player?explorerAmber:npcRole;
            ring.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
            for(int i=0;i<48;i++){float a=i*Mathf.PI/24;ring.SetPosition(i,new Vector3(Mathf.Cos(a)*.43f,.025f,Mathf.Sin(a)*.43f));}
        }
        void RemapSeal(GameObject model)
        {
            foreach(var renderer in model.GetComponentsInChildren<Renderer>())
            {
                var mats=renderer.sharedMaterials;
                for(int i=0;i<mats.Length;i++)
                {
                    string name=mats[i]!=null?mats[i].name:"";
                    var replacement=name.Contains("Cream")?FocaCream:name.Contains("Eyelids")?FocaEyelids:name.Contains("Eyes")?FocaEyes:name.Contains("Nose")?FocaNose:name.Contains("Whiskers")?FocaWhiskers:FocaSkin;
                    if(replacement!=null)mats[i]=replacement;
                }
                renderer.sharedMaterials=mats;
            }
        }
        void UpdateCharacterCamera()
        {
            if(Rig.Follow==null)return;
            var kind=Rig.Follow==explorer?PlayerCharacter:NpcCharacter;
            Rig.FollowHeight=kind==CharacterKind.FocaWatona?.32f:.65f;
        }

        public void BeginRoute()
        {
            if(!Ready())return;Following=false;
            if(Navigator.CurrentCell==GoalCell)ResetDemo();
            Navigator.SetPaused(false);Navigator.RequestTrace=ShowExploration;Navigator.GoTo(GoalCell);marker.position=GoalCell.ToWorld();Notify(NpcCharacterName+" explora el jardín hacia el faro dorado.");
        }

        public void ResetDemo()
        {
            if(Navigator==null)return;
            Following=false;GateClosed=false;Sealed=false;manual.Clear();Navigator.Initialize(Client,Map,StartCell,Navigator.VisualRoot);World.SyncObstacles(Navigator.Blocked);
            marker.position=GoalCell.ToWorld();Rig.ResetView();ExploreMode=false;explorer.gameObject.SetActive(false);Notify("Recorrido restaurado. El mismo mapa, listo para otro experimento.");
        }

        public void ToggleGate()=>ChangePreset(true);
        public void ToggleSeal()=>ChangePreset(false);
        void ChangePreset(bool isGate)
        {
            if(!Ready())return;
            bool nextGate=isGate?!GateClosed:GateClosed,nextSeal=isGate?Sealed:!Sealed;
            var cells=new HashSet<GridCell>(manual);if(nextGate)cells.UnionWith(gate);if(nextSeal)cells.UnionWith(seal);
            if(!ClearOfExplorer(cells)||!Navigator.SetBlocked(cells)){Notify("Espera a que los guardianes abandonen la zona antes de cerrar el paso.");return;}
            GateClosed=nextGate;Sealed=nextSeal;World.SyncObstacles(cells);
            Notify(isGate?(GateClosed?"Compuerta cerrada. El motor calcula un desvío.":"Compuerta abierta. El paso vuelve a estar disponible."):(Sealed?"Pasadizo sellado. Comprueba si el destino sigue siendo alcanzable.":"Pasadizo liberado. El motor vuelve a buscar una ruta."));
        }

        public void TogglePause(){if(Navigator!=null){Navigator.SetPaused(!Navigator.IsPaused);Notify(Navigator.IsPaused?"Simulación en pausa.":"Simulación reanudada.");}}
        public void SetAlgorithm(string value){if(!Ready())return;Navigator.SetAlgorithm(value);Notify("Algoritmo: "+value+". La búsqueda sigue ejecutándose en Python.");}
        public void ToggleRoute(){ShowRoute=!ShowRoute;if(path)path.enabled=ShowRoute;Changed?.Invoke();}
        public void ToggleTrace(){ShowExploration=!ShowExploration;Navigator.RequestTrace=ShowExploration;if(ShowExploration&&Navigator.HasDestination)Navigator.Replan();else if(traceObject)traceObject.SetActive(false);Changed?.Invoke();}
        public void ToggleCamera()
        {
            if(Rig.Follow==Navigator.transform){Rig.ResetView();}
            else{Rig.Follow=Navigator.transform;Rig.CloseView=true;Rig.Distance=6;Rig.Pitch=33;}
            UpdateCharacterCamera();
            Changed?.Invoke();
        }
        public void ToggleExplore()
        {
            ExploreMode=!ExploreMode;explorer.gameObject.SetActive(ExploreMode);Following=false;
            if(ExploreMode)
            {
                explorer.position=Navigator.CurrentCell.ToWorld()+Vector3.right;
                if(!CanStand(explorer.position))explorer.position=Navigator.CurrentCell.ToWorld();
                Rig.Follow=explorer;Rig.CloseView=true;Rig.Distance=7;Rig.Pitch=38;
                UpdateCharacterCamera();
                Notify("Explorador: WASD para caminar. G llama a "+NpcCharacterName+". E acciona la compuerta.");
            }
            else{Rig.ResetView();Notify("Vista táctica. Clic para ordenar un destino; Shift + clic para colocar una barrera.");}
        }
        public void ToggleFollow(){if(!ExploreMode||!Ready())return;Following=!Following;followAt=0;Notify(Following?NpcCharacterName+" te acompaña. Se actualizará el destino al cambiar de celda.":NpcCharacterName+" mantiene su última orden.");}
        bool Ready(){if(Online&&Navigator!=null)return true;Notify("El motor debe estar conectado para calcular rutas. Pulsa Reconectar.");return false;}
        public void Notify(string text){Message=text;Changed?.Invoke();}

        void OnRoute(RouteResult result)
        {
            if(path==null)return;
            path.positionCount=result.Route.Length;for(int i=0;i<result.Route.Length;i++)path.SetPosition(i,result.Route[i].ToWorld(.055f));path.enabled=ShowRoute;
            if(!result.Found)Notify("No hay ruta. Abre el pasadizo o retira obstáculos para continuar.");
            else Changed?.Invoke();
            ClearTrace();
            if(ShowExploration&&result.Trace.Length>0)
            {
                var draft=new MeshDraft();var seen=new HashSet<GridCell>();
                foreach(var e in result.Trace)if(e.Type=="expandido"&&seen.Add(e.Position))draft.Box(e.Position.ToWorld(.022f),new Vector3(.72f,.012f,.72f));
                traceObject=new GameObject("Nodos explorados por Python");traceObject.AddComponent<MeshFilter>().sharedMesh=draft.Create();traceObject.AddComponent<MeshRenderer>().sharedMaterial=World.Material("Exploracion",new Color(.18f,.42f,.37f),0,.2f);
            }
        }
        void ClearTrace(){if(traceObject){var mesh=traceObject.GetComponent<MeshFilter>().sharedMesh;Destroy(traceObject);Destroy(mesh);}}

        void Update()
        {
            if(Navigator==null)return;
            if(Input.GetKeyDown(KeyCode.Space))TogglePause();if(Input.GetKeyDown(KeyCode.E))ToggleGate();if(Input.GetKeyDown(KeyCode.R))ResetDemo();
            if(Input.GetKeyDown(KeyCode.Tab))ToggleExplore();if(Input.GetKeyDown(KeyCode.F))ToggleCamera();if(Input.GetKeyDown(KeyCode.G))ToggleFollow();
            if(ExploreMode)MoveExplorer();
            if(Online&&Following&&Time.time>=followAt&&Vector3.Distance(explorer.position,Navigator.transform.position)>2.5f)
            {followAt=Time.time+1.2f;var target=GridCell.FromWorld(explorer.position);Navigator.GoTo(target);marker.position=target.ToWorld();}
            if(Input.GetMouseButtonDown(0)&&(EventSystem.current==null||!EventSystem.current.IsPointerOverGameObject()))
            {
                Ray ray=Rig.GetComponent<Camera>().ScreenPointToRay(Input.mousePosition);
                if(new Plane(Vector3.up,Vector3.zero).Raycast(ray,out float distance))
                {
                    GridCell target=GridCell.FromWorld(ray.GetPoint(distance));if(!Map.IsWalkable(target)||!Ready())return;
                    if(Input.GetKey(KeyCode.LeftShift)||Input.GetKey(KeyCode.RightShift))
                    {
                        var proposed=new HashSet<GridCell>(manual);if(!proposed.Remove(target))proposed.Add(target);
                        var all=new HashSet<GridCell>(proposed);if(GateClosed)all.UnionWith(gate);if(Sealed)all.UnionWith(seal);
                        if(ClearOfExplorer(all)&&Navigator.SetBlocked(all)){manual.Clear();manual.UnionWith(proposed);World.SyncObstacles(all);Notify("Obstáculos actualizados desde la posición actual del compañero.");}else Notify("La celda está ocupada por un guardián o es el destino del compañero.");
                    }
                    else if(Navigator.GoTo(target)){Following=false;marker.position=target.ToWorld();Notify("Destino seleccionado: "+target+".");}
                }
            }
            if(marker)marker.rotation=Quaternion.Euler(0,Time.time*12,0);
        }

        void MoveExplorer()
        {
            if(Navigator.IsPaused)return;
            Vector3 right=Rig.transform.right;right.y=0;right.Normalize();Vector3 forward=Vector3.Cross(right,Vector3.up);
            Vector3 direction=Vector3.ClampMagnitude(right*Input.GetAxisRaw("Horizontal")+forward*Input.GetAxisRaw("Vertical"),1);
            // Bound the spatial step so a slow frame cannot jump over a one-cell wall.
            Vector3 next=explorer.position+direction*(Input.GetKey(KeyCode.LeftShift)?3.5f:2.3f)*Mathf.Min(Time.deltaTime,.05f);
            if(CanStand(next))explorer.position=next;
            else {Vector3 x=new Vector3(next.x,0,explorer.position.z);if(CanStand(x))explorer.position=x;Vector3 z=new Vector3(explorer.position.x,0,next.z);if(CanStand(z))explorer.position=z;}
            if(direction.sqrMagnitude>.01f)explorer.GetChild(0).rotation=Quaternion.Slerp(explorer.GetChild(0).rotation,Quaternion.LookRotation(direction),Time.deltaTime*12);
        }
        bool CanStand(Vector3 p)
        {
            var blocked=new HashSet<GridCell>(Navigator.Blocked);
            foreach(Vector3 o in new[]{new Vector3(-.23f,0,-.23f),new Vector3(.23f,0,-.23f),new Vector3(-.23f,0,.23f),new Vector3(.23f,0,.23f)})
            {var cell=GridCell.FromWorld(p+o);if(!Map.IsWalkable(cell)||blocked.Contains(cell))return false;}
            return true;
        }
        bool ClearOfExplorer(HashSet<GridCell> cells)
        {
            if(!ExploreMode)return true;
            foreach(Vector3 o in new[]{new Vector3(-.23f,0,-.23f),new Vector3(.23f,0,-.23f),new Vector3(-.23f,0,.23f),new Vector3(.23f,0,.23f)})
                if(cells.Contains(GridCell.FromWorld(explorer.position+o)))return false;
            return true;
        }
        void OnDestroy(){if(explorerAmber)Destroy(explorerAmber);if(npcRole)Destroy(npcRole);}
    }
}
