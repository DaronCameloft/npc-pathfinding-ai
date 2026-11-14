using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Arcadia;
using Arcadia.Navigation;
using UnityEngine;
using Newtonsoft.Json;

// Run only in Play Mode:
// unity command 'script run' --file ../tools/PlayChecks.cs --entry PlayChecks.Run
// No Unity scene or source assets are changed. Evidence is written only on execution.
public static class PlayChecks
{
    const double InitialCost = 51.35533905932736;
    const double GateCost = 57.94112549695427;
    const double MovingGateCost = 41.798989873223334;
    const double Tolerance = 1e-8;
    static bool running;

    [Serializable]
    public sealed class Check
    {
        public string name, status, algorithm, state, detail, error, stack;
        public double elapsedMs, cost, expectedCost, algorithmMs;
        public bool hasCost, hasExpectedCost;
        public int[] routeStart, routeGoal, currentCell;
        public int routeCells, expanded, replans;
    }

    [Serializable]
    public sealed class Report
    {
        public string status = "running";
        public string startedUtc, finishedUtc, unityVersion, transport, map, error, stack;
        public int passed, failed;
        public double elapsedMs;
        public bool restored;
        public List<Check> checks = new List<Check>();
    }

    public static async Task<object> Run()
    {
        if (running) return new { status = "busy", message = "PlayChecks is already running." };
        running = true;
        var watch = Stopwatch.StartNew();
        var report = new Report { startedUtc = DateTime.UtcNow.ToString("o"), unityVersion = Application.unityVersion };
        string projectRoot = Directory.GetParent(Application.dataPath).FullName;
        string output = Path.GetFullPath(Path.Combine(projectRoot, "../docs/play-checks.json"));
        ArcadiaGame game = null;
        NpcNavigator npc = null;
        float originalSpeed = 0;
        string originalAlgorithm = "astar";
        bool originalTrace = false, originalRequestTrace = false, originalRoute = true;
        bool saved = false;
        int mainThread = Thread.CurrentThread.ManagedThreadId;

        try
        {
            Require(Application.isPlaying, "Enter Play Mode before running PlayChecks.");
            Require(SynchronizationContext.Current != null, "A Unity synchronization context is required.");
            game = UnityEngine.Object.FindAnyObjectByType<ArcadiaGame>();
            Require(game != null, "No active ArcadiaGame was found.");
            await Until(() => game.Navigator != null && game.Online, "ArcadiaGame initialization and API connection", mainThread);
            npc = game.Navigator;
            Require(npc.enabled && npc.gameObject.activeInHierarchy, "The NPC must initially be enabled and active.");
            originalSpeed = npc.Speed; originalAlgorithm = npc.Algorithm;
            originalTrace = game.ShowExploration; originalRequestTrace = npc.RequestTrace; originalRoute = game.ShowRoute;
            saved = true;
            report.transport = game.Client.BaseUrl; report.map = game.Map.Name;
            Require(report.map == "den011d", "These reference costs belong to den011d.");
            Require(game.StartCell == new GridCell(106, 123) && game.GoalCell == new GridCell(107, 92), "Demo endpoints differ from scenario 124.");
            game.ShowExploration = false; npc.RequestTrace = false;

            await Case(report, "initial_astar_from_start", async check =>
            {
                Reset(game, "astar");
                RouteResult result = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                ValidateFound(game, result, game.StartCell, check, InitialCost);
                Require(npc.IsPaused && npc.State == NavigationState.Paused, "NPC must be paused immediately after issuing the request.");
                AtCell(npc, game.StartCell, "Initial HTTP response must not advance the actor.");
                check.detail = "Initial request completed while movement stayed paused; reference from demo-smoke-http.json.";
            });

            await Case(report, "closed_gate_from_start", async check =>
            {
                Reset(game, "astar");
                await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                RouteResult result = await Fresh(game, () => game.ToggleGate(), mainThread);
                Require(game.GateClosed && npc.Blocked.Count == 8, "Gate must block its eight configured cells.");
                ValidateFound(game, result, game.StartCell, check, GateCost);
                AtCell(npc, game.StartCell, "Gate replan must stay at the starting cell while paused.");
            });

            await Case(report, "gate_and_seal_no_route", async check =>
            {
                Reset(game, "astar"); game.ToggleGate(); game.ToggleSeal();
                Require(game.GateClosed && game.Sealed && npc.Blocked.Count == 10, "Both obstacle presets must be active.");
                RouteResult result = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                Evidence(check, npc, result);
                Require(result.Status == "sin_ruta" && !result.Found && result.Route.Length == 0 && !result.Cost.HasValue, "Isolated destination must return a genuine no-route result.");
                Require(npc.ActiveRoute.Count == 0, "No-route must clear the active route.");
                npc.SetPaused(false);
                Require(npc.State == NavigationState.NoRoute, "Underlying navigation state must be NoRoute.");
                await Task.Delay(150);
                AtCell(npc, game.StartCell, "An NPC without a route must remain still.");
                npc.SetPaused(true);
                check.state = NavigationState.NoRoute.ToString();
            });

            await Case(report, "unblock_recovery", async check =>
            {
                Reset(game, "astar"); game.ToggleGate(); game.ToggleSeal();
                RouteResult isolated = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                Require(!isolated.Found, "Recovery setup must begin without a route.");
                RouteResult gateOnly = await Fresh(game, () => game.ToggleSeal(), mainThread);
                ValidateFound(game, gateOnly, game.StartCell, check, GateCost);
                RouteResult reopened = await Fresh(game, () => game.ToggleGate(), mainThread);
                ValidateFound(game, reopened, game.StartCell, check, InitialCost);
                Require(!game.GateClosed && !game.Sealed && npc.Blocked.Count == 0, "Reopening must remove both obstacle presets.");
                check.detail = "Opening the sealed passage restores the detour; opening the gate restores the original cost.";
            });

            foreach (string selected in new[] { "astar", "dijkstra", "bfs", "voraz" })
            {
                string algorithm = selected;
                await Case(report, "algorithm_" + algorithm, async check =>
                {
                    Reset(game, "astar");
                    await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                    RouteResult result = await Fresh(game, () =>
                    {
                        if (npc.Algorithm == algorithm) npc.Replan();
                        else game.SetAlgorithm(algorithm);
                    }, mainThread);
                    Require(result.Algorithm == algorithm && npc.Algorithm == algorithm, "Selected algorithm must match the response.");
                    ValidateFound(game, result, game.StartCell, check, algorithm == "astar" || algorithm == "dijkstra" ? (double?)InitialCost : null);
                    Require(result.Cost.Value >= InitialCost - Tolerance, "A returned route cannot cost less than the known optimum.");
                    check.detail = "Algorithm switched through the live client; every returned step and route cost were checked.";
                });
            }

            await Case(report, "real_movement_pause_resume", async check =>
            {
                Reset(game, "astar"); npc.Speed = 4;
                RouteResult result = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                ValidateFound(game, result, game.StartCell, check, InitialCost);
                npc.SetPaused(false);
                await Until(() => npc.CurrentCell != game.StartCell, "First completed movement waypoint", mainThread, npc);
                npc.SetPaused(true);
                Vector3 position = npc.transform.position;
                GridCell cell = npc.CurrentCell;
                float travelled = npc.DistanceTravelled;
                Require(travelled > 0 && Vector3.Distance(position, npc.WorldPosition(game.StartCell)) > .5f, "Transform must actually move in Play Mode.");
                await Task.Delay(300);
                Require(npc.CurrentCell == cell && Vector3.Distance(npc.transform.position, position) < 0.00001f && Math.Abs(npc.DistanceTravelled - travelled) < 0.00001f, "Pause must freeze position, completed cell and travelled distance.");
                npc.SetPaused(false);
                await Until(() => npc.DistanceTravelled > travelled + .5f, "Movement after resume", mainThread, npc);
                npc.SetPaused(true);
                check.currentCell = Pair(npc.CurrentCell); check.state = npc.State.ToString();
                check.detail = "Observed physical movement, 300 ms of stable pause, then additional movement after resuming.";
            });

            await Case(report, "current_cell_replan_against_dijkstra", async check =>
            {
                Reset(game, "astar"); npc.Speed = 12;
                RouteResult first = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                Require(first.Route.Length > 12, "Reference route needs waypoint 12.");
                GridCell origin = first.Route[12];
                Require(origin == new GridCell(96, 111), "The moving-replan reference waypoint has changed.");
                await MoveToWaypoint(npc, origin, mainThread);
                AtCell(npc, origin, "Waypoint pause must stop exactly at the completed cell.");
                RouteResult replanned = await Fresh(game, () => game.ToggleGate(), mainThread);
                Require(game.GateClosed, "Gate must close for current-cell replan.");
                ValidateFound(game, replanned, origin, check, MovingGateCost);
                Require(replanned.Route[0] != game.StartCell && npc.ReplanCount > 0, "A moving replan must not restart from the original spawn.");
                RouteResult oracle = await Fresh(game, () => game.SetAlgorithm("dijkstra"), mainThread);
                ValidateFound(game, oracle, origin, new Check(), MovingGateCost);
                Require(Math.Abs(oracle.Cost.Value - replanned.Cost.Value) < Tolerance, "A* replan must match Dijkstra for the same origin and obstacles.");
                check.detail = "Moved to route[12], closed the gate, replanned from (96,111), and independently matched the Dijkstra result.";
            });

            await Case(report, "mid_edge_change_returns_to_safe_cell", async check =>
            {
                Reset(game, "astar"); npc.Speed = 2;
                RouteResult first = await Fresh(game, () => { game.BeginRoute(); npc.SetPaused(true); }, mainThread);
                await MoveToWaypoint(npc, first.Route[2], mainThread);
                npc.SetPaused(false);
                await Until(() => Vector3.Distance(npc.transform.position, npc.WorldPosition(npc.CurrentCell)) > .2f, "Movement between waypoint centers", mainThread, npc);
                npc.SetPaused(true);
                GridCell origin = npc.CurrentCell;
                Require(origin != game.StartCell, "Mid-edge replan must start after actual progress.");
                Require(Vector3.Distance(npc.transform.position, npc.WorldPosition(origin)) > .15f, "The test must actually interrupt an edge.");
                int priorReplans = npc.ReplanCount;
                RouteResult result = await Fresh(game, () =>
                {
                    game.ToggleGate();
                    Require(game.GateClosed && npc.ActiveRoute.Count == 0, "Obstacle change must invalidate the route immediately.");
                    npc.SetPaused(false);
                    Require(npc.State == NavigationState.ReturningToCell, "In-flight movement must return along its safe edge before requesting a new route.");
                }, mainThread);
                ValidateFound(game, result, origin, check);
                AtCell(npc, origin, "The new response must start at the exact safe cell, not the spawn or rounded transform position.");
                Require(npc.ReplanCount == priorReplans + 1, "One obstacle change should produce one replan after the return.");
                check.detail = "Closed a gate while the actor was between cells; observed ReturningToCell, then a fresh HTTP route from the last completed cell.";
            });

            foreach (bool disableObject in new[] { false, true })
            {
                bool objectLifecycle = disableObject;
                await Case(report, objectLifecycle ? "gameobject_disable_reenable_during_planning" : "component_disable_reenable_during_planning", async check =>
                {
                    Reset(game, "astar");
                    RouteResult accepted = null;
                    int responses = 0;
                    Action<RouteResult> receive = result => { accepted = result; responses++; npc.SetPaused(true); };
                    npc.RouteChanged += receive;
                    try
                    {
                        game.BeginRoute();
                        Require(npc.State == NavigationState.Planning && npc.LastResult == null, "Disable must occur while a genuine HTTP query is pending.");
                        if (objectLifecycle) npc.gameObject.SetActive(false); else npc.enabled = false;
                        Require(npc.State == NavigationState.Idle && npc.HasDestination, "OnDisable must cancel planning while retaining the requested destination.");
                        await Task.Delay(250);
                        Require(responses == 0 && npc.LastResult == null, "The cancelled query must not deliver a stale result.");
                        if (objectLifecycle) npc.gameObject.SetActive(true); else npc.enabled = true;
                        npc.SetPaused(true);
                        await Until(() => accepted != null, "New request after re-enabling NPC", mainThread, npc);
                        ValidateFound(game, accepted, game.StartCell, check, InitialCost);
                        AtCell(npc, game.StartCell, "Re-enabled NPC must preserve its safe starting position.");
                        await Task.Delay(150);
                        Require(responses == 1, "Exactly one live result should arrive after cancellation and reactivation.");
                        check.detail = "Real Play lifecycle cancelled an in-flight query, suppressed its result, and automatically issued a fresh query on enable.";
                    }
                    finally
                    {
                        npc.RouteChanged -= receive;
                        // Cancel first, then reactivate: cleanup must not accidentally restart a failed test query.
                        npc.ResetTo(game.StartCell);
                        npc.enabled = true;
                        npc.gameObject.SetActive(true);
                    }
                });
            }
        }
        catch (Exception error)
        {
            report.error = error.Message; report.stack = error.ToString();
        }
        finally
        {
            if (saved && game != null && npc != null)
            {
                try
                {
                    npc.ResetTo(game.StartCell);
                    npc.enabled = true; npc.gameObject.SetActive(true);
                    game.ResetDemo();
                    npc.Speed = originalSpeed;
                    game.ShowExploration = originalTrace; npc.RequestTrace = originalRequestTrace;
                    if (game.ShowRoute != originalRoute) game.ToggleRoute();
                    npc.SetAlgorithm(originalAlgorithm);
                    Require(npc.State == NavigationState.Idle && !npc.HasDestination && npc.Blocked.Count == 0, "Cleanup failed to restore the idle demo.");
                    AtCell(npc, game.StartCell, "Cleanup failed to restore the spawn position.");
                    report.restored = true;
                }
                catch (Exception error)
                {
                    report.error = (report.error ?? "") + " Cleanup: " + error.Message;
                    report.stack = (report.stack ?? "") + Environment.NewLine + error;
                }
            }
            report.passed = report.checks.Count(check => check.status == "passed");
            report.failed = report.checks.Count(check => check.status == "failed");
            report.status = report.failed == 0 && string.IsNullOrEmpty(report.error) && report.restored && report.checks.Count > 0 ? "passed" : "failed";
            report.finishedUtc = DateTime.UtcNow.ToString("o"); report.elapsedMs = watch.Elapsed.TotalMilliseconds;
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(output));
                File.WriteAllText(output, JsonConvert.SerializeObject(report, Formatting.Indented) + Environment.NewLine);
            }
            catch (Exception error)
            {
                report.status = "failed"; report.error = (report.error ?? "") + " Report write: " + error.Message;
            }
            running = false;
        }

        return new
        {
            status = report.status,
            passed = report.passed,
            failed = report.failed,
            restored = report.restored,
            reportPath = output,
            elapsedMs = report.elapsedMs,
            error = report.error,
            failedChecks = report.checks.Where(check => check.status == "failed").Select(check => new { name = check.name, error = check.error }).ToArray()
        };
    }

    static void Reset(ArcadiaGame game, string algorithm)
    {
        Require(game != null && game.Online, "The engine must remain online during Play checks.");
        var npc = game.Navigator;
        npc.ResetTo(game.StartCell); npc.enabled = true; npc.gameObject.SetActive(true);
        game.ResetDemo(); game.SetAlgorithm(algorithm);
        game.ShowExploration = false; npc.RequestTrace = false;
    }

    static async Task Case(Report report, string name, Func<Check, Task> action)
    {
        var check = new Check { name = name, status = "running" };
        var watch = Stopwatch.StartNew(); report.checks.Add(check);
        try { await action(check); check.status = "passed"; }
        catch (Exception error) { check.status = "failed"; check.error = error.Message; check.stack = error.ToString(); }
        finally { check.elapsedMs = watch.Elapsed.TotalMilliseconds; }
    }

    static async Task<RouteResult> Fresh(ArcadiaGame game, Action request, int mainThread)
    {
        Require(game.Online, "Motor must be online before issuing a request.");
        var npc = game.Navigator;
        RouteResult received = null;
        string failure = null;
        Action<RouteResult> receive = result => { received = result; npc.SetPaused(true); };
        Action<string> fail = message => failure = message;
        npc.RouteChanged += receive; npc.Error += fail;
        try
        {
            request();
            await Until(() => received != null || failure != null, "Fresh HTTP route response", mainThread, npc);
            Require(failure == null, failure ?? "HTTP request failed.");
            Require(received != null && ReferenceEquals(received, npc.LastResult), "Only the fresh accepted route result may satisfy this check.");
            return received;
        }
        finally { npc.RouteChanged -= receive; npc.Error -= fail; }
    }

    static async Task MoveToWaypoint(NpcNavigator npc, GridCell target, int mainThread)
    {
        bool reached = false;
        Action<GridCell> stop = cell => { if (cell == target) { npc.SetPaused(true); reached = true; } };
        npc.CellReached += stop;
        try
        {
            npc.SetPaused(false);
            await Until(() => reached, "Movement to waypoint " + target, mainThread, npc);
        }
        finally { npc.CellReached -= stop; }
    }

    static async Task Until(Func<bool> condition, string description, int mainThread, NpcNavigator npc = null)
    {
        var watch = Stopwatch.StartNew();
        while (!condition())
        {
            Require(Application.isPlaying, "Play Mode ended during: " + description);
            Require(Thread.CurrentThread.ManagedThreadId == mainThread, "Lost Unity main-thread context during: " + description);
            if (npc != null && !string.IsNullOrEmpty(npc.LastError)) throw new Exception(description + ": " + npc.LastError);
            if (watch.Elapsed.TotalSeconds >= 10) throw new TimeoutException(description + " exceeded 10 seconds.");
            // Captures UnitySynchronizationContext. Never block Update/coroutines with Thread.Sleep or .Wait().
            await Task.Delay(25);
        }
        Require(Thread.CurrentThread.ManagedThreadId == mainThread, "Continuation left Unity's main thread.");
    }

    static void ValidateFound(ArcadiaGame game, RouteResult result, GridCell origin, Check check, double? expected = null)
    {
        Evidence(check, game.Navigator, result);
        if (expected.HasValue) { check.hasExpectedCost = true; check.expectedCost = expected.Value; }
        Require(result != null && result.Found && result.Cost.HasValue, "Expected a found route with a numeric cost.");
        Require(RouteValidation.IsLegal(game.Map, new HashSet<GridCell>(game.Navigator.Blocked), origin, game.GoalCell, result), "Returned route violates endpoints, walkability or no-corner-cutting rules.");
        double measured = 0;
        for (int i = 1; i < result.Route.Length; i++)
        {
            GridCell a = result.Route[i - 1], b = result.Route[i];
            measured += a.Row != b.Row && a.Column != b.Column ? Math.Sqrt(2) : 1;
        }
        Require(Math.Abs(result.Cost.Value - measured) < Tolerance, "Reported route cost disagrees with the returned steps.");
        if (expected.HasValue) Require(Math.Abs(result.Cost.Value - expected.Value) < Tolerance, "Expected cost " + expected.Value.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + ", received " + result.Cost.Value.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + ".");
    }

    static void Evidence(Check check, NpcNavigator npc, RouteResult result)
    {
        check.state = npc.State.ToString(); check.currentCell = Pair(npc.CurrentCell); check.replans = npc.ReplanCount;
        if (result == null) return;
        check.algorithm = result.Algorithm; check.routeCells = result.Route.Length;
        check.hasCost = result.Cost.HasValue; check.cost = result.Cost ?? 0;
        check.expanded = result.Metrics.Expanded; check.algorithmMs = result.Metrics.Milliseconds;
        if (result.Route.Length > 0) { check.routeStart = Pair(result.Route[0]); check.routeGoal = Pair(result.Route[result.Route.Length - 1]); }
    }

    static int[] Pair(GridCell cell) => new[] { cell.Row, cell.Column };
    static void AtCell(NpcNavigator npc, GridCell cell, string message) => Require(npc.CurrentCell == cell && Vector3.Distance(npc.transform.position, npc.WorldPosition(cell)) < 0.00001f, message);
    static void Require(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
}
