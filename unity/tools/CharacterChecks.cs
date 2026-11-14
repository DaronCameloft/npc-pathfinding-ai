using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Arcadia;
using Arcadia.Navigation;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// Play Mode, with the local engine running. Do not interact during this check.
// unity command 'script run' --file ../tools/CharacterChecks.cs --entry CharacterChecks.Run --timeout 55 --json
public static class CharacterChecks
{
    const string NpcKey="Arcadia.Character.Npc",PlayerKey="Arcadia.Character.Player";
    static bool running;
    sealed class Check { public string name,status,error; public double elapsedMs; }
    sealed class Report
    {
        public string status="running",startedUtc,finishedUtc,unityVersion,error;
        public int passed,failed;
        public bool restored;
        public List<Check> checks=new List<Check>();
    }
    sealed class Snapshot
    {
        public Transform wrapper,playerWrapper,cameraTarget;
        public Vector3 position,playerPosition;
        public Quaternion rotation,playerRotation;
        public GridCell cell,destination;
        public GridCell[] route,blocked;
        public RouteResult result;
        public NavigationState state;
        public int routeIndex,replans;
        public float distance;
        public bool paused,hasDestination,following,exploring;
    }

    public static async Task<object> Run()
    {
        if(running)return new {status="busy"};
        running=true;
        var report=new Report{startedUtc=DateTime.UtcNow.ToString("o"),unityVersion=Application.unityVersion};
        string output=Path.GetFullPath(Path.Combine(Application.dataPath,"../../docs/character-checks.json"));
        var game=UnityEngine.Object.FindAnyObjectByType<ArcadiaGame>();
        bool npcKeyExisted=PlayerPrefs.HasKey(NpcKey),playerKeyExisted=PlayerPrefs.HasKey(PlayerKey);
        int npcPref=PlayerPrefs.GetInt(NpcKey),playerPref=PlayerPrefs.GetInt(PlayerKey);
        CharacterKind originalNpc=CharacterKind.Auri,originalPlayer=CharacterKind.Auri;
        string originalAlgorithm="astar";
        float originalSpeed=2.6f;
        bool saved=false;
        try
        {
            Require(Application.isPlaying&&game!=null,"Play Mode with Arcadia is required.");
            await Until(()=>game.Navigator!=null&&game.Online,"Game initialization and engine connection");
            Require(game.AuriModel!=null&&game.FocaWatonaModel!=null,"Both imported model prefabs are required.");
            originalNpc=game.NpcCharacter;originalPlayer=game.PlayerCharacter;
            originalAlgorithm=game.Navigator.Algorithm;originalSpeed=game.Navigator.Speed;saved=true;

            await Case(report,"independent_choices_with_hidden_player",async()=>
            {
                Defaults(game);
                var npcRoot=game.Navigator.transform;
                var playerRoot=game.PlayerRoot;
                game.SetNpcCharacter(CharacterKind.FocaWatona);
                Require(game.NpcCharacter==CharacterKind.FocaWatona&&game.PlayerCharacter==CharacterKind.Auri,"NPC choice changed the player's selection.");
                game.SetPlayerCharacter(CharacterKind.FocaWatona);
                Require(game.NpcCharacter==CharacterKind.FocaWatona&&game.PlayerCharacter==CharacterKind.FocaWatona,"The two roles cannot use the same model.");
                game.SetPlayerCharacter(CharacterKind.Auri);
                await Task.Delay(100);
                Require(game.NpcCharacter==CharacterKind.FocaWatona&&game.PlayerCharacter==CharacterKind.Auri,"Player choice changed the NPC's selection.");
                Require(game.Navigator.transform==npcRoot&&game.PlayerRoot==playerRoot&&!game.PlayerRoot.gameObject.activeSelf,"Changing a hidden player must preserve its root and visibility.");
                Require(!game.Navigator.HasDestination&&game.Navigator.LastResult==null,"Appearance selection unexpectedly started navigation.");
            });

            await Case(report,"paused_route_and_obstacles_survive_model_changes",async()=>
            {
                Defaults(game);game.ToggleGate();game.ToggleCamera();
                game.BeginRoute();game.Navigator.SetPaused(true);
                await Until(()=>game.Navigator.LastResult!=null,"Paused route response");
                Require(game.Navigator.LastResult.Found&&game.Navigator.Blocked.Count==8,"Expected a valid route with the closed gate.");
                var before=Capture(game);
                game.SetNpcCharacter(CharacterKind.FocaWatona);game.SetPlayerCharacter(CharacterKind.FocaWatona);
                Unchanged(game,before);
                await Task.Delay(150);
                Unchanged(game,before);
                Require(game.GateClosed,"Changing appearance reopened the gate.");
            });

            await Case(report,"moving_npc_continues_same_route_without_replanning",async()=>
            {
                Defaults(game);game.Navigator.Speed=.8f;game.ToggleCamera();game.BeginRoute();
                await Until(()=>game.Navigator.IsMoving&&game.Navigator.DistanceTravelled>.06f,"Start actual NPC movement");
                var before=Capture(game);
                game.SetNpcCharacter(CharacterKind.FocaWatona);
                Unchanged(game,before);
                await Task.Delay(250);
                Require(game.Navigator.DistanceTravelled>before.distance,"NPC stopped after changing its model.");
                Require(ReferenceEquals(game.Navigator.LastResult,before.result)&&game.Navigator.ReplanCount==before.replans,"Appearance change recalculated the live route.");
                Require(game.Navigator.Destination==before.destination&&game.Rig.Follow==before.cameraTarget,"Appearance change lost destination or follow camera.");
                game.Navigator.SetPaused(true);
            });

            await Case(report,"player_following_and_camera_survive_both_choices",async()=>
            {
                Defaults(game);game.ToggleExplore();game.ToggleFollow();game.Navigator.SetPaused(true);
                Require(game.Following&&game.Rig.Follow==game.PlayerRoot,"Failed to establish player-following mode.");
                var before=Capture(game);
                game.SetPlayerCharacter(CharacterKind.FocaWatona);game.SetNpcCharacter(CharacterKind.FocaWatona);
                await Task.Delay(100);
                Unchanged(game,before);
                Require(game.PlayerRoot.gameObject.activeSelf,"Visible player disappeared after selection.");
            });

            await Case(report,"both_seals_have_valid_art_and_distinct_role_indicators",async()=>
            {
                Defaults(game);game.ToggleExplore();
                game.SetNpcCharacter(CharacterKind.FocaWatona);game.SetPlayerCharacter(CharacterKind.FocaWatona);
                await Task.Delay(150);
                ValidateSeal(game.Navigator.VisualRoot);
                ValidateSeal(game.PlayerRoot.GetChild(0));
                var npcRing=game.Navigator.VisualRoot.GetComponentsInChildren<LineRenderer>().Single();
                var playerRing=game.PlayerRoot.GetComponentsInChildren<LineRenderer>().Single();
                Require(npcRing.sharedMaterial!=playerRing.sharedMaterial,"Identical models need distinct NPC/player role indicators.");
                Require(npcRing.sharedMaterial.color!=playerRing.sharedMaterial.color,"Role indicators have the same color.");
            });

            await Case(report,"selector_buttons_release_focus_and_preserve_navigation",async()=>
            {
                Defaults(game);
                var panel=GameObject.Find("Selector de personajes");
                Require(panel!=null&&EventSystem.current!=null,"Character selector or EventSystem is missing.");
                var buttons=panel.GetComponentsInChildren<Button>().Where(b=>b.name=="Foca Watona")
                    .OrderByDescending(b=>b.GetComponent<RectTransform>().anchoredPosition.y).ToArray();
                Require(buttons.Length==2,"Expected one seal button for each role.");
                var before=Capture(game);
                foreach(var button in buttons)
                {
                    EventSystem.current.SetSelectedGameObject(button.gameObject);button.onClick.Invoke();
                    Require(EventSystem.current.currentSelectedGameObject==null,"Selector retained keyboard focus, risking accidental Space submission.");
                }
                await Task.Delay(100);Unchanged(game,before);
                Require(game.NpcCharacter==CharacterKind.FocaWatona&&game.PlayerCharacter==CharacterKind.FocaWatona,"Selector actions did not independently select both roles.");
                Require(PlayerPrefs.GetInt(NpcKey,-1)==1&&PlayerPrefs.GetInt(PlayerKey,-1)==1,"Selections were not saved independently.");
            });

            await Case(report,"reset_keeps_choices_and_removes_experiment_state",async()=>
            {
                Defaults(game);game.SetNpcCharacter(CharacterKind.FocaWatona);game.ToggleGate();game.ToggleExplore();game.ToggleFollow();
                var npcWrapper=game.Navigator.VisualRoot;var playerWrapper=game.PlayerRoot.GetChild(0);
                game.ResetDemo();await Task.Delay(100);
                Require(game.NpcCharacter==CharacterKind.FocaWatona&&game.PlayerCharacter==CharacterKind.Auri,"Reset discarded character choices.");
                Require(game.Navigator.VisualRoot==npcWrapper&&game.PlayerRoot.GetChild(0)==playerWrapper,"Reset replaced the stable actor wrappers.");
                Require(game.Navigator.CurrentCell==game.StartCell&&game.Navigator.Blocked.Count==0&&!game.Navigator.HasDestination,"Reset did not clear the navigation experiment.");
                Require(!game.ExploreMode&&!game.Following&&!game.PlayerRoot.gameObject.activeSelf&&!game.GateClosed,"Reset did not restore idle demonstration state.");
            });

            await Case(report,"repeated_changes_leave_one_active_model_per_role",async()=>
            {
                Defaults(game);game.ToggleExplore();
                for(int i=0;i<4;i++)
                {
                    game.SetNpcCharacter(CharacterKind.FocaWatona);game.SetPlayerCharacter(CharacterKind.FocaWatona);
                    game.SetNpcCharacter(CharacterKind.Auri);game.SetPlayerCharacter(CharacterKind.Auri);
                }
                await Task.Delay(150);
                foreach(var root in new[]{game.Navigator.VisualRoot,game.PlayerRoot.GetChild(0)})
                {
                    Require(root.GetComponentsInChildren<AuriMotion>(true).Length==1,"Repeated choices left duplicate robot models.");
                    Require(root.GetComponentsInChildren<SealMotion>(true).Length==0,"Old seal animation or geometry survived replacement.");
                    Require(root.GetComponentsInChildren<LineRenderer>(true).Length==1,"Repeated choices left duplicate role indicators.");
                    Require(root.childCount==2,"Expected exactly one model and one role indicator after deferred destruction.");
                }
            });
        }
        catch(Exception error){report.error=error.ToString();}
        finally
        {
            try
            {
                if(saved&&game!=null&&game.Navigator!=null)
                {
                    game.ResetDemo();game.Navigator.Speed=originalSpeed;game.Navigator.SetAlgorithm(originalAlgorithm);
                    game.SetNpcCharacter(originalNpc);game.SetPlayerCharacter(originalPlayer);
                    await Task.Delay(100);
                    Require(game.NpcCharacter==originalNpc&&game.PlayerCharacter==originalPlayer,"Original selections could not be restored.");
                    Require(!game.Navigator.HasDestination&&game.Navigator.CurrentCell==game.StartCell,"Cleanup did not restore the idle demo.");
                    report.restored=true;
                }
            }
            catch(Exception error){report.error=(report.error??"")+" Cleanup: "+error;}
            finally
            {
                RestorePreference(NpcKey,npcKeyExisted,npcPref);RestorePreference(PlayerKey,playerKeyExisted,playerPref);PlayerPrefs.Save();
                running=false;
            }
            report.passed=report.checks.Count(c=>c.status=="passed");report.failed=report.checks.Count(c=>c.status=="failed");
            report.finishedUtc=DateTime.UtcNow.ToString("o");
            report.status=report.passed==8&&report.failed==0&&report.restored&&string.IsNullOrEmpty(report.error)?"passed":"failed";
            try{Directory.CreateDirectory(Path.GetDirectoryName(output));File.WriteAllText(output,JsonConvert.SerializeObject(report,Formatting.Indented)+Environment.NewLine);}
            catch(Exception error){report.status="failed";report.error=(report.error??"")+" Report write: "+error.Message;}
        }
        return new{status=report.status,passed=report.passed,failed=report.failed,restored=report.restored,reportPath=output,error=report.error,
            failedChecks=report.checks.Where(c=>c.status=="failed").Select(c=>new{name=c.name,error=c.error}).ToArray()};
    }

    static void Defaults(ArcadiaGame game)
    {
        game.ResetDemo();game.Navigator.Speed=2.6f;game.SetAlgorithm("astar");
        game.SetNpcCharacter(CharacterKind.Auri);game.SetPlayerCharacter(CharacterKind.Auri);
    }
    static Snapshot Capture(ArcadiaGame game)
    {
        var n=game.Navigator;var playerWrapper=game.PlayerRoot.GetChild(0);
        return new Snapshot{wrapper=n.VisualRoot,playerWrapper=playerWrapper,position=n.transform.position,playerPosition=game.PlayerRoot.position,
            rotation=n.VisualRoot.rotation,playerRotation=playerWrapper.rotation,cell=n.CurrentCell,destination=n.Destination,hasDestination=n.HasDestination,
            route=n.ActiveRoute.ToArray(),blocked=n.Blocked.ToArray(),result=n.LastResult,state=n.State,routeIndex=n.RouteIndex,replans=n.ReplanCount,
            distance=n.DistanceTravelled,paused=n.IsPaused,following=game.Following,exploring=game.ExploreMode,cameraTarget=game.Rig.Follow};
    }
    static void Unchanged(ArcadiaGame game,Snapshot before)
    {
        var n=game.Navigator;
        Require(n.VisualRoot==before.wrapper&&game.PlayerRoot.GetChild(0)==before.playerWrapper,"An actor's stable facing wrapper was replaced.");
        Require(Vector3.Distance(n.transform.position,before.position)<.00001f&&Vector3.Distance(game.PlayerRoot.position,before.playerPosition)<.00001f,"Appearance change moved an actor.");
        Require(Quaternion.Angle(n.VisualRoot.rotation,before.rotation)<.01f&&Quaternion.Angle(game.PlayerRoot.GetChild(0).rotation,before.playerRotation)<.01f,"Appearance change rotated the navigation wrapper.");
        Require(n.CurrentCell==before.cell&&n.Destination==before.destination&&n.HasDestination==before.hasDestination,"Appearance change modified navigation endpoints.");
        Require(n.ActiveRoute.SequenceEqual(before.route)&&n.RouteIndex==before.routeIndex&&new HashSet<GridCell>(n.Blocked).SetEquals(before.blocked),"Appearance change modified the route, progress or obstacles.");
        Require(ReferenceEquals(n.LastResult,before.result)&&n.ReplanCount==before.replans&&Mathf.Abs(n.DistanceTravelled-before.distance)<.00001f,"Appearance change replaced route metrics or triggered another search.");
        Require(n.State==before.state&&n.IsPaused==before.paused,"Appearance change modified movement/pause state.");
        Require(game.Following==before.following&&game.ExploreMode==before.exploring&&game.Rig.Follow==before.cameraTarget,"Appearance change modified following, exploration or camera target.");
    }
    static void ValidateSeal(Transform root)
    {
        Require(root.GetComponentsInChildren<SealMotion>(true).Length==1&&root.GetComponentsInChildren<AuriMotion>(true).Length==0,"Expected exactly one seal animation and no stale robot.");
        var renderers=root.GetComponentsInChildren<MeshRenderer>();
        Require(renderers.Length>0,"Seal has no visible meshes.");
        bool hasTexture=false;
        foreach(var renderer in renderers)foreach(var material in renderer.sharedMaterials)
        {
            Require(material!=null&&material.shader!=null&&material.shader.name=="Universal Render Pipeline/Lit","Seal has an invalid or non-URP material.");
            if(material.HasProperty("_BaseMap")&&material.GetTexture("_BaseMap")!=null)hasTexture=true;
        }
        Require(hasTexture,"Seal's mottled skin texture is missing.");
    }
    static async Task Case(Report report,string name,Func<Task> action)
    {
        var check=new Check{name=name,status="running"};report.checks.Add(check);var watch=Stopwatch.StartNew();
        try{await action();check.status="passed";}catch(Exception error){check.status="failed";check.error=error.ToString();}
        finally{check.elapsedMs=watch.Elapsed.TotalMilliseconds;}
    }
    static async Task Until(Func<bool> condition,string label)
    {
        var watch=Stopwatch.StartNew();while(!condition())
        {Require(Application.isPlaying,"Play Mode ended during "+label);if(watch.Elapsed.TotalSeconds>9)throw new TimeoutException(label);await Task.Delay(25);}
    }
    static void RestorePreference(string key,bool existed,int value){if(existed)PlayerPrefs.SetInt(key,value);else PlayerPrefs.DeleteKey(key);}
    static void Require(bool condition,string message){if(!condition)throw new InvalidOperationException(message);}
}
