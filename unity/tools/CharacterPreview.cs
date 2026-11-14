using System.Linq;
using Arcadia;
using UnityEngine;

public static class CharacterPreview
{
    public static object Show()
    {
        var game=Object.FindAnyObjectByType<ArcadiaGame>();
        game.ResetDemo();game.SetNpcCharacter(CharacterKind.FocaWatona);game.SetPlayerCharacter(CharacterKind.Auri);
        game.Navigator.VisualRoot.rotation=Quaternion.identity;
        game.ToggleExplore();
        game.PlayerRoot.GetChild(0).rotation=Quaternion.identity;
        game.Rig.Follow=null;game.Rig.CloseView=true;
        game.Rig.Focus=game.Navigator.transform.position+new Vector3(.4f,.35f,0);
        game.Rig.Distance=4.7f;game.Rig.Pitch=27;game.Rig.Yaw=18;game.Rig.Snap();
        return Inspect();
    }
    public static object Inspect()
    {
        var game=Object.FindAnyObjectByType<ArcadiaGame>();
        return new { npc=game.NpcCharacterName,player=game.PlayerCharacterName,
            models=game.Navigator.GetComponentsInChildren<Renderer>().Select(r=>new { name=r.name,bounds=r.bounds.ToString(),materials=r.sharedMaterials.Select(m=>m.name).ToArray() }).ToArray() };
    }
}
