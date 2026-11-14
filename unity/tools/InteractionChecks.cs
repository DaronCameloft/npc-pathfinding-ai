using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading.Tasks;
using Arcadia;
using Arcadia.Navigation;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public static class InteractionChecks
{
    public static async Task<object> Run()
    {
        var game=UnityEngine.Object.FindAnyObjectByType<ArcadiaGame>();
        if(!Application.isPlaying||game==null||!game.Online)throw new Exception("Play Mode and an online engine are required.");
        string url=game.Client.BaseUrl;
        int passed=0;
        try
        {
            game.ResetDemo();game.ToggleExplore();
            var explorer=(Transform)typeof(ArcadiaGame).GetField("explorer",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(game);
            explorer.position=new GridCell(90,99).ToWorld();game.ToggleGate();
            Assert(!game.GateClosed&&game.Navigator.Blocked.Count==0,"Gate must not close on the explorer.");passed++;
            var safe=typeof(ArcadiaGame).GetMethod("ClearOfExplorer",BindingFlags.Instance|BindingFlags.NonPublic);
            Assert(!(bool)safe.Invoke(game,new object[]{new HashSet<GridCell>{new GridCell(90,99)}}),"Manual barriers must protect explorer footprint.");passed++;
            game.ResetDemo();game.ToggleExplore();game.ToggleFollow();
            Assert(game.Following,"Follow setup failed.");game.Client.BaseUrl="invalid-local-url";
            game.Navigator.GoTo(game.GoalCell);
            await Task.Delay(100);
            Assert(!game.Following&&!game.Online&&game.Navigator.State==NavigationState.Error,"Engine failure must stop automatic following.");passed++;
            game.Client.BaseUrl=url;game.Reconnect();
            var deadline=DateTime.UtcNow.AddSeconds(8);
            while(!game.Online&&DateTime.UtcNow<deadline)await Task.Delay(25);
            Assert(game.Online,"Reconnect failed.");passed++;
            game.ResetDemo();
            foreach(var button in UnityEngine.Object.FindObjectsByType<Button>(FindObjectsSortMode.None))
                if(button.name=="Iniciar recorrido")
                {
                    EventSystem.current.SetSelectedGameObject(button.gameObject);button.onClick.Invoke();
                    Assert(EventSystem.current.currentSelectedGameObject==null,"Button must release selection so Space only pauses.");passed++;break;
                }
            Assert(passed==5,"Start button was not found.");
            return new {status="passed",passed,checks="Explorer barriers, engine failure, reconnect, UI focus"};
        }
        finally {game.Client.BaseUrl=url;game.ResetDemo();}
    }
    static void Assert(bool value,string error){if(!value)throw new Exception(error);}
}
