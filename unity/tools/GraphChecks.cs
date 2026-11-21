using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Arcadia;
using Arcadia.Navigation;
using Newtonsoft.Json;
using UnityEditor;
using UnityEngine;

// Execute through Unity Pipeline in Play Mode, with the local API running.
public static class GraphChecks
{
    static void Check(bool condition,string message)
    {
        if(!condition)throw new Exception(message);
    }

    static async Task Wait(Func<bool> condition,GardenModes modes)
    {
        double deadline=EditorApplication.timeSinceStartup+30;
        while(!condition())
        {
            Check(!modes.Failed,modes.Status);
            Check(EditorApplication.timeSinceStartup<deadline,"Tiempo agotado: "+modes.Status);
            await Task.Delay(20);
        }
    }

    static async Task Capture(string path)
    {
        await Task.Delay(350);
        var previous=File.GetLastWriteTimeUtc(path);
        ScreenCapture.CaptureScreenshot(path);
        for(int i=0;i<100 && File.GetLastWriteTimeUtc(path)==previous;i++)await Task.Delay(50);
        Check(File.Exists(path) && File.GetLastWriteTimeUtc(path)!=previous,"Captura pendiente: "+path);
    }

    public static async Task<object> Run()
    {
        var game=UnityEngine.Object.FindAnyObjectByType<ArcadiaGame>();
        var modes=game.Modes;
        var results=new List<object>();
        string docs=Path.GetFullPath(Path.Combine(Application.dataPath,"../../docs"));
        var view=EditorWindow.GetWindow(typeof(EditorWindow).Assembly.GetType("UnityEditor.GameView"));
        bool maximized=view.maximized;
        float oldScale=Time.timeScale;
        string originalAlgorithm=game.Navigator.Algorithm;
        try
        {
            view.maximized=true;view.Focus();
            modes.Select(GardenMode.Navigation);
            game.ResetDemo();game.SetAlgorithm("astar");game.BeginRoute();game.Navigator.SetPaused(true);
            await Wait(()=>game.Navigator.Session!=null,modes);
            game.ToggleGate();
            await Wait(()=>game.Navigator.Session.Current["astar"].Reason=="obstaculos",modes);
            var cell=game.Navigator.CurrentCell;
            var id=game.Navigator.Session.Id;
            var barriers=game.Navigator.Blocked.ToArray();
            modes.Select(GardenMode.Corridor);
            await Wait(()=>modes.Ready,modes);
            var corridor=modes.Corridor;
            Check(corridor.celdas==1816 && corridor.entradas.Length==45 && corridor.salidas.Length==44,"Dimensiones del pasillo");
            Check(corridor.corte.SequenceEqual(new[]{new GridCell(30,173),new GridCell(30,174),new GridCell(30,175)}),"Corte inesperado");
            Check(corridor.flujo_maximo==3 && corridor.aumentos.Length==3 && corridor.caminos.All(r=>r.Length==60),"Flujo y caminos");
            var lanes=corridor.caminos.Select(r=>new HashSet<GridCell>(r)).ToArray();
            Check(lanes.Length==3 && !lanes[0].Overlaps(lanes[1]) && !lanes[0].Overlaps(lanes[2]) && !lanes[1].Overlaps(lanes[2]),"Las rutas comparten celdas");
            var actors=modes.Scene.Cast<Transform>().Where(t=>t.name.StartsWith("Guardián de pasillo")).ToArray();
            Check(actors.Length==3,"Faltan guardianes simultáneos");
            var start=actors.Select(t=>t.position).ToArray();
            await Capture(Path.Combine(docs,"pasillo.png"));
            Check(actors.Select((t,i)=>t.position!=start[i]).All(v=>v),"Los tres guardianes deben moverse");
            modes.ToggleCut();await Wait(()=>modes.Ready,modes);
            Check(modes.Corridor.flujo_maximo==0 && modes.Corridor.caminos.Length==0 && modes.Scene.Cast<Transform>().Count(t=>t.name=="Barrera del corte" && t.GetComponent<Collider>().enabled)==3,"Cierre físico y flujo cero");
            results.Add(new {mode="pasillo",openFlow=3,closedFlow=0,agents=actors.Length,disjoint=true,cells=corridor.celdas});
            modes.ToggleCut();await Wait(()=>modes.Ready,modes);
            Check(modes.Corridor.flujo_maximo==3,"Reapertura del pasillo");

            modes.Select(GardenMode.Patrol);await Wait(()=>modes.Ready,modes);
            var network=modes.Patrol;
            int drawn=modes.Scene.Cast<Transform>().Count(t=>t.name=="Tramo del árbol");
            Check(drawn==6 && network.arbol.Length==6 && network.candidatas.Length==21 && network.decisiones.Length==9,"Red de Kruskal");
            Check(Math.Abs(network.costo_arbol-624.7595)<.001 && Math.Abs(network.costo_candidatas-3253.447)<.01 && network.componentes==1,"Costos de patrullaje");
            await Capture(Path.Combine(docs,"patrullaje.png"));
            var actor=modes.Scene.Find("Auri de patrullaje");
            modes.StartPatrol();Time.timeScale=8;
            await Wait(()=>Vector3.Distance(actor.position,network.puntos[0].ToWorld())>3,modes);
            await Wait(()=>!modes.Walking,modes);
            Check(Vector3.Distance(actor.position,network.puntos[0].ToWorld())<.01f,"El DFS debe regresar a P1");
            results.Add(new {mode="patrullaje",drawn,network.costo_arbol,network.costo_candidatas,returnedToStart=true});
            modes.OtherPoints();await Wait(()=>modes.Ready,modes);
            Check(!network.puntos.SequenceEqual(modes.Patrol.puntos),"Otros puntos debe usar la siguiente semilla");
            Time.timeScale=oldScale;

            modes.Select(GardenMode.Loot);await Wait(()=>modes.Ready,modes);
            modes.OpenChest();await Wait(()=>modes.Ready,modes);
            var loot=modes.Loot;
            Check(loot.capacidad==20 && loot.optima.valor==113 && loot.voraz.valor==99 && loot.optima.peso==20 && loot.voraz.peso==17,"Selección de botín");
            Check(loot.optima.elegidos.SequenceEqual(new[]{0,3,4,5,6,10,11}) && loot.tabla.Length==13 && loot.tabla.All(r=>r.Length==21),"Objetos y tabla");
            Check(modes.VisibleRows==13 && modes.Reconstructed==loot.reconstruccion.Length,"Reconstrucción incompleta");
            await Capture(Path.Combine(docs,"botin.png"));
            modes.SetCapacity(25);await Wait(()=>modes.Ready,modes);
            Check(modes.Loot.optima.valor==139 && modes.Loot.voraz.valor==139,"Cambio de capacidad");
            results.Add(new {mode="botin",optimalAt20=loot.optima.valor,greedyAt20=loot.voraz.valor,optimalAt25=modes.Loot.optima.valor});
            modes.Select(GardenMode.Navigation);await Task.Delay(100);
            Check(game.Navigator.CurrentCell==cell && game.Navigator.Session.Id==id && game.Navigator.IsPaused,"Se perdió el recorrido de navegación");
            Check(game.GateClosed && new HashSet<GridCell>(barriers).SetEquals(game.World.Obstacles.Keys),"Barreras de navegación");
            Check(modes.Scene==null && !game.transform.Cast<Transform>().Any(t=>t.name.StartsWith("Experimento ")),"Dibujos huérfanos");
            results.Add(new {mode="navegacion",sessionPreserved=true,obstaclesRestored=true});
            return new {passed=results.Count};
        }
        finally
        {
            Time.timeScale=oldScale;modes.Select(GardenMode.Navigation);game.ResetDemo();
            game.SetAlgorithm(originalAlgorithm);view.maximized=maximized;
            var report=new {utc=DateTime.UtcNow,unity=Application.unityVersion,passed=results.Count,results};
            File.WriteAllText(Path.Combine(docs,"graph-checks.json"),JsonConvert.SerializeObject(report,Formatting.Indented));
        }
    }
}
