using UnityEngine;
using UnityEditor;
using Arcadia;
public static class EditorQA
{
    public static object Prepare() { Arcadia.Editor.ArcadiaBuilder.PrepareAndCheck(); return "checks passed"; }
    public static object Status() {
        var game=Object.FindAnyObjectByType<ArcadiaGame>();
        if(game==null || game.Navigator==null) return new { playing=Application.isPlaying, loaded=false };
        var npc=game.Navigator;
        return new { playing=Application.isPlaying, online=game.Online, state=npc.State.ToString(), cell=npc.CurrentCell.ToString(), position=npc.transform.position.ToString(), goal=npc.Destination.ToString(), route=npc.ActiveRoute.Count, cost=npc.LastResult?.Cost, error=npc.LastError };
    }
    public static object Build() { Arcadia.Editor.ArcadiaBuilder.BuildWindows(); return "build passed"; }
    public static object Inspect() {
        var game=Object.FindAnyObjectByType<ArcadiaGame>();
        var list=new System.Collections.Generic.List<object>();
        foreach(var t in game.Navigator.GetComponentsInChildren<Transform>()) if(t.name.Contains("Pivot")||t.name=="Auri") list.Add(new {name=t.name, local=t.localPosition.ToString(), rot=t.localEulerAngles.ToString(), scale=t.lossyScale.ToString()});
        return new { camera=Camera.main.transform.position.ToString(),focus=game.Rig.Focus.ToString(), models=list };
    }
    public static object Portrait() {
        var g=Object.FindAnyObjectByType<ArcadiaGame>();
        g.Navigator.VisualRoot.rotation=Quaternion.identity;
        g.Rig.Follow=g.Navigator.transform;g.Rig.CloseView=true;g.Rig.Focus=g.Navigator.transform.position+Vector3.up*.5f;g.Rig.Distance=4;g.Rig.Pitch=25;g.Rig.Yaw=20;g.Rig.Snap();
        return Inspect();
    }
    public static async System.Threading.Tasks.Task<object> CameraWalk() {
        var g=Object.FindAnyObjectByType<ArcadiaGame>();
        g.ResetDemo();g.ToggleCamera();g.BeginRoute();
        await System.Threading.Tasks.Task.Delay(2200);g.TogglePause();
        return Status();
    }
}
