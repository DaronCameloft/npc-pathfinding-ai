using System;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using Arcadia.Navigation;

namespace Arcadia
{
    public sealed class ArcadiaHud : MonoBehaviour
    {
        ArcadiaGame game;
        Font font;
        RectTransform canvas;
        RectTransform comparison;
        Text astarMetrics, incrementalMetrics;
        Text connection,message,state,cost,time,nodes,replans,position,mode;
        Text gateLabel,sealLabel,pauseLabel,followLabel,missionTitle;
        Text npcAuri,npcSeal,playerAuri,playerSeal;
        Texture2D minimap;
        RawImage mapImage;
        float mapAt,refreshAt;
        readonly Color cream=new Color(.95f,.92f,.82f),muted=new Color(.64f,.70f,.62f),mint=new Color(.41f,.89f,.72f);
        readonly Color ink=new Color(.035f,.075f,.065f,.94f);
        Sprite rounded;
        readonly System.Collections.Generic.Dictionary<string,Text> algorithmButtons=new System.Collections.Generic.Dictionary<string,Text>();

        public void Initialize(ArcadiaGame owner)
        {
            game=owner;font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            rounded=RoundedSprite();
            var root=new GameObject("Arcadia interface",typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));
            var c=root.GetComponent<Canvas>();c.renderMode=RenderMode.ScreenSpaceOverlay;c.sortingOrder=20;
            var scaler=root.GetComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=new Vector2(1600,900);scaler.matchWidthOrHeight=.5f;
            canvas=root.GetComponent<RectTransform>();
            if(FindAnyObjectByType<EventSystem>()==null){var events=new GameObject("EventSystem",typeof(EventSystem),typeof(StandaloneInputModule));}

            // The world remains the main canvas. Floating cards use restrained botanical colors.
            var header=Panel("Marca",canvas,32,27,380,100,new Color(.025f,.055f,.04f,.82f));
            Label(header,"A R C A D I A",24,15,330,32,28,cream,FontStyle.Bold);
            Label(header,"EL JARDIN DE LOS GUARDIANES",25,55,330,20,11,mint,FontStyle.Normal);
            var mission=Panel("Mision",canvas,32,143,300,112,ink);
            Label(mission,"01  /  EL DESPERTAR",18,15,268,20,11,mint,FontStyle.Bold);
            missionTitle=Label(mission,"Guía a Auri al faro",18,42,268,25,18,cream,FontStyle.Bold);
            Label(mission,"Cierra el paso. Descubre otro camino.",18,76,268,20,12,muted);

            var characters=Panel("Selector de personajes",canvas,32,271,300,198,ink);
            Label(characters,"ELIGE TUS GUARDIANES",18,15,264,20,11,mint,FontStyle.Bold);
            Label(characters,"COMPAÑERO · NPC",18,44,264,16,10,muted,FontStyle.Bold);
            npcAuri=Button(characters,"Auri",18,65,96,32,()=>game.SetNpcCharacter(CharacterKind.Auri));
            npcSeal=Button(characters,"Foca Watona",122,65,160,32,()=>game.SetNpcCharacter(CharacterKind.FocaWatona));
            Label(characters,"TU PERSONAJE · WASD",18,111,264,16,10,muted,FontStyle.Bold);
            playerAuri=Button(characters,"Auri",18,132,96,32,()=>game.SetPlayerCharacter(CharacterKind.Auri));
            playerSeal=Button(characters,"Foca Watona",122,132,160,32,()=>game.SetPlayerCharacter(CharacterKind.FocaWatona));
            Label(characters,"● Seleccionado · Cambia mientras juegas",18,177,264,16,10,muted);

            var observatory=Panel("Observatorio",canvas,-298,27,266,440,ink,true);
            connection=Label(observatory,"CONECTANDO",18,16,230,20,11,mint,FontStyle.Bold);
            Label(observatory,"Santuario de Den",18,46,230,25,21,cream,FontStyle.Bold);
            Label(observatory,"DEN011D  /  MAPA ORIGINAL",18,77,230,16,10,muted);
            var mapObj=new GameObject("Cartografia",typeof(RectTransform),typeof(RawImage));mapObj.transform.SetParent(observatory,false);
            SetRect(mapObj.GetComponent<RectTransform>(),18,108,230,146);mapImage=mapObj.GetComponent<RawImage>();mapImage.raycastTarget=false;
            minimap=new Texture2D(196,144,TextureFormat.RGBA32,false);minimap.filterMode=FilterMode.Point;mapImage.texture=minimap;
            state=Label(observatory,"EN ESPERA",18,269,230,22,13,mint,FontStyle.Bold);
            cost=Metric(observatory,"COSTO DE RUTA",18,310,105);
            time=Metric(observatory,"PLANIFICACION",142,310,105);
            nodes=Metric(observatory,"NODOS",18,369,105);
            replans=Metric(observatory,"RECALCULOS",142,369,105);

            comparison=Panel("Comparación",canvas,346,143,370,142,ink);
            astarMetrics=Label(comparison,"",14,12,172,124,14,cream);
            incrementalMetrics=Label(comparison,"",190,12,172,124,14,mint);
            var actions=Panel("Acciones",canvas,-298,483,266,264,ink,true);
            Label(actions,"INTERACTUAR",18,15,230,20,11,muted,FontStyle.Bold);
            gateLabel=Button(actions,"Cerrar compuerta  [E]",18,45,230,36,()=>game.ToggleGate(),true);
            sealLabel=Button(actions,"Sellar pasadizo",18,88,230,36,()=>game.ToggleSeal());
            Button(actions,"Retirar barreras / reiniciar  [R]",18,131,230,34,()=>game.ResetDemo());
            Button(actions,"Ver ruta",18,174,110,30,()=>game.ToggleRoute());
            Button(actions,"Ver búsqueda",138,174,110,30,()=>game.ToggleTrace());
            Button(actions,"Reconectar motor",18,215,230,29,()=>game.Reconnect());

            var lower=Panel("Controles",canvas,32,-134,1012,102,ink,false,true);
            mode=Label(lower,"VISTA TACTICA",20,13,155,18,11,mint,FontStyle.Bold);
            Button(lower,"Iniciar recorrido",20,42,160,39,()=>game.BeginRoute(),true);
            pauseLabel=Button(lower,"Pausar  [Espacio]",190,42,155,39,()=>game.TogglePause());
            Button(lower,"Explorar  [Tab]",355,42,150,39,()=>game.ToggleExplore());
            Button(lower,"Seguir cámara  [F]",515,42,160,39,()=>game.ToggleCamera());
            followLabel=Button(lower,"Auri, sígueme  [G]",685,42,160,39,()=>game.ToggleFollow());
            Button(lower,"Reiniciar",855,42,135,39,()=>game.ResetDemo());
            Label(lower,"CLIC  destino     SHIFT + CLIC  barrera     RUEDA  zoom     BOTON DERECHO  orbitar",190,13,790,18,11,muted);

            var algorithm=Panel("Algoritmos",canvas,32,-200,650,50,new Color(.035f,.075f,.065f,.90f),false,true);
            Label(algorithm,"BUSQUEDA",16,17,90,16,10,muted,FontStyle.Bold);
            algorithmButtons["astar"]=Button(algorithm,"A*",112,9,90,32,()=>game.SetAlgorithm("astar"),true);
            algorithmButtons["dijkstra"]=Button(algorithm,"Dijkstra",210,9,110,32,()=>game.SetAlgorithm("dijkstra"));
            algorithmButtons["bfs"]=Button(algorithm,"BFS",328,9,90,32,()=>game.SetAlgorithm("bfs"));
            algorithmButtons["voraz"]=Button(algorithm,"Voraz",426,9,90,32,()=>game.SetAlgorithm("voraz"));

            algorithmButtons["dstar_lite"]=Button(algorithm,"D* Lite",524,9,110,32,()=>game.SetAlgorithm("dstar_lite"));
            var status=Panel("Mensaje",canvas,32,-247,1012,35,new Color(.03f,.06f,.045f,.78f),false,true);
            message=Label(status,game.Message,14,7,985,22,12,cream);
            position=Label(canvas,"",34,-24,900,18,10,new Color(.82f,.85f,.75f),FontStyle.Normal,false,true);
            game.Changed+=Refresh;Refresh();
        }

        Text Metric(Transform parent,string label,float x,float y,float width)
        {Label(parent,label,x,y,width,15,9,muted,FontStyle.Bold);return Label(parent,"—",x,y+18,width,28,22,cream);}

        void CharacterButton(Text button,string label,bool selected)
        {
            button.text=selected?"● "+label:label;
            button.fontStyle=selected?FontStyle.Bold:FontStyle.Normal;
            button.color=selected?cream:muted;
            button.transform.parent.GetComponent<Image>().color=selected?new Color(.26f,.47f,.35f):new Color(.12f,.19f,.15f);
        }

        RectTransform Panel(string name,Transform parent,float x,float y,float w,float h,Color color,bool right=false,bool bottom=false)
        {
            var o=new GameObject(name,typeof(RectTransform),typeof(Image));o.transform.SetParent(parent,false);var r=o.GetComponent<RectTransform>();SetRect(r,x,y,w,h,right,bottom);
            var image=o.GetComponent<Image>();image.sprite=rounded;image.type=Image.Type.Sliced;image.color=color;return r;
        }
        Text Label(Transform parent,string value,float x,float y,float w,float h,int size,Color color,FontStyle style=FontStyle.Normal,bool right=false,bool bottom=false)
        {
            var o=new GameObject(value,typeof(RectTransform),typeof(Text));o.transform.SetParent(parent,false);SetRect(o.GetComponent<RectTransform>(),x,y,w,h,right,bottom);
            var text=o.GetComponent<Text>();text.font=font;text.text=value;text.fontSize=size;text.color=color;text.fontStyle=style;text.raycastTarget=false;text.horizontalOverflow=HorizontalWrapMode.Wrap;text.verticalOverflow=VerticalWrapMode.Truncate;return text;
        }
        Text Button(Transform parent,string label,float x,float y,float w,float h,Action action,bool accent=false)
        {
            var p=Panel(label,parent,x,y,w,h,accent?new Color(.26f,.47f,.35f):new Color(.12f,.19f,.15f));
            var b=p.gameObject.AddComponent<Button>();var colors=b.colors;colors.normalColor=Color.white;colors.highlightedColor=new Color(1.17f,1.17f,1.17f);colors.pressedColor=new Color(.8f,.9f,.83f);colors.selectedColor=Color.white;b.colors=colors;b.onClick.AddListener(()=>{EventSystem.current?.SetSelectedGameObject(null);action();});
            var t=Label(p,label,5,0,w-10,h,12,cream,accent?FontStyle.Bold:FontStyle.Normal);t.alignment=TextAnchor.MiddleCenter;return t;
        }
        static void SetRect(RectTransform r,float x,float y,float w,float h,bool right=false,bool bottom=false)
        {r.anchorMin=r.anchorMax=new Vector2(right?1:0,bottom?0:1);r.pivot=new Vector2(0,1);r.anchoredPosition=new Vector2(x,-y);r.sizeDelta=new Vector2(w,h);}
        Sprite RoundedSprite()
        {
            const int n=32;var t=new Texture2D(n,n,TextureFormat.RGBA32,false);t.wrapMode=TextureWrapMode.Clamp;
            var pixels=new Color[n*n];for(int y=0;y<n;y++)for(int x=0;x<n;x++){float dx=Mathf.Max(7-x,x-(n-8)),dy=Mathf.Max(7-y,y-(n-8));float d=Mathf.Sqrt(Mathf.Max(dx,0)*Mathf.Max(dx,0)+Mathf.Max(dy,0)*Mathf.Max(dy,0));pixels[y*n+x]=new Color(1,1,1,Mathf.Clamp01(7.5f-d));}t.SetPixels(pixels);t.Apply();return Sprite.Create(t,new Rect(0,0,n,n),new Vector2(.5f,.5f),100,0,SpriteMeshType.FullRect,new Vector4(8,8,8,8));
        }

        void Update()
        {
            if(game==null||game.Navigator==null)return;
            if(Time.unscaledTime>=refreshAt){Refresh();refreshAt=Time.unscaledTime+.2f;}
            if(Time.unscaledTime>=mapAt){DrawMap();mapAt=Time.unscaledTime+.25f;}
        }
        void Refresh()
        {
            if(connection==null||game.Navigator==null)return;
            var n=game.Navigator;connection.text=game.Connection;connection.color=game.Online?mint:new Color(1,.65f,.35f);message.text=game.Message;
            missionTitle.text="Guía a "+game.NpcCharacterName+" al faro";
            CharacterButton(npcAuri,"Auri",game.NpcCharacter==CharacterKind.Auri);
            CharacterButton(npcSeal,"Foca Watona",game.NpcCharacter==CharacterKind.FocaWatona);
            CharacterButton(playerAuri,"Auri",game.PlayerCharacter==CharacterKind.Auri);
            CharacterButton(playerSeal,"Foca Watona",game.PlayerCharacter==CharacterKind.FocaWatona);
            string s=n.State==NavigationState.Moving?"EN CAMINO":n.State==NavigationState.Planning?"BUSCANDO RUTA":n.State==NavigationState.Arrived?"DESTINO ALCANZADO":n.State==NavigationState.NoRoute?"SIN RUTA":n.State==NavigationState.Paused?"EN PAUSA":n.State==NavigationState.Error?"ERROR DE CONEXION":n.State==NavigationState.ReturningToCell?"AJUSTANDO POSICION":"EN ESPERA";
            state.text=s+"  /  "+n.Algorithm.ToUpperInvariant();var result=n.LastResult;
            foreach(var pair in algorithmButtons)pair.Value.transform.parent.GetComponent<Image>().color=pair.Key==n.Algorithm?new Color(.26f,.47f,.35f):new Color(.12f,.19f,.15f);
            cost.text=result?.Cost.HasValue==true?result.Cost.Value.ToString("0.00"):"—";time.text=result!=null?result.Metrics.Milliseconds.ToString("0.0")+" ms":"—";nodes.text=result!=null?result.Metrics.Expanded.ToString():"—";replans.text=n.ReplanCount.ToString();
            comparison.gameObject.SetActive(n.Session != null);
            if (n.Session != null)
            {
                var a = n.Session.Current["astar"].Result;
                var d = n.Session.Current["dstar_lite"].Result;
                astarMetrics.text = Describe("A* · completo", a, n);
                incrementalMetrics.text = Describe("D* Lite · incremental", d, n);
                if (n.Renewed) message.text = "Sesión renovada. " + message.text;
                if (a.Cost.HasValue != d.Cost.HasValue || Math.Abs(a.Cost.GetValueOrDefault()-d.Cost.GetValueOrDefault()) > 0.000001)
                    message.text = "Los costos del motor difieren. " + message.text;
            }
            gateLabel.text=game.GateClosed?"Abrir compuerta  [E]":"Cerrar compuerta  [E]";sealLabel.text=game.Sealed?"Liberar pasadizo":"Sellar pasadizo";pauseLabel.text=n.IsPaused?"Continuar  [Espacio]":"Pausar  [Espacio]";
            mode.text=game.ExploreMode?"EXPLORACION / WASD":game.Rig.Follow!=null?"CAMARA DEL NPC":"VISTA TACTICA";
            followLabel.text=game.Following?"Dejar de seguir  [G]":game.NpcCharacterName+", sígueme  [G]";
            followLabel.fontSize=game.NpcCharacter==CharacterKind.FocaWatona&&!game.Following?10:12;
            position.text="ARCADIALABS    /    NPC: "+game.NpcCharacterName.ToUpperInvariant()+" "+n.CurrentCell+"    /    TU PERSONAJE: "+game.PlayerCharacterName.ToUpperInvariant()+"    /    "+n.DistanceTravelled.ToString("0.0")+" u recorridas    /    "+n.Blocked.Count+" celdas bloqueadas";
        }
        static string Describe(string title, RouteResult result, NpcNavigator npc)
        {
            npc.ExpandedTotals.TryGetValue(result.Algorithm, out int total);
            return title + "\nCosto  " + (result.Cost?.ToString("0.0000") ?? "sin ruta")
                + "\n" + result.Metrics.Milliseconds.ToString("0.00") + " ms"
                + "\n" + result.Metrics.Expanded + " nodos"
                + "\n" + total + " acumulados";
        }

        void DrawMap()
        {
            if(minimap==null||game.Map==null)return;
            const int minC=84,minR=80;var blocked=new System.Collections.Generic.HashSet<GridCell>(game.Navigator.Blocked);var route=new System.Collections.Generic.HashSet<GridCell>(game.Navigator.ActiveRoute);
            var pixels=new Color32[minimap.width*minimap.height];
            for(int y=0;y<minimap.height;y++)for(int x=0;x<minimap.width;x++)
            {
                var cell=new GridCell(minR+y/4,minC+x/4);Color color=game.Map.IsWalkable(cell)?new Color(.32f,.39f,.29f):new Color(.075f,.13f,.10f);
                if(game.ShowRoute&&route.Contains(cell))color=new Color(.24f,.69f,.52f);if(blocked.Contains(cell))color=new Color(.81f,.41f,.19f);
                if(cell==(game.Navigator.HasDestination?game.Navigator.Destination:game.GoalCell))color=new Color(1,.75f,.30f);if(cell==game.Navigator.CurrentCell)color=Color.white;pixels[y*minimap.width+x]=color;
            }
            minimap.SetPixels32(pixels);minimap.Apply();
        }
        void OnDestroy(){if(game!=null)game.Changed-=Refresh;if(minimap)Destroy(minimap);if(rounded){Destroy(rounded.texture);Destroy(rounded);}if(canvas)Destroy(canvas.gameObject);}
    }
}
