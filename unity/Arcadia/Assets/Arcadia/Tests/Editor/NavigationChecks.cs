using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace Arcadia.Navigation.Editor
{
    /// <summary>Dependency-free editor checks. Throws on failure for batch-mode validation.</summary>
    public static class NavigationChecks
    {
        private static int assertions;
        private const string FoundJson = "{\"algoritmo\":\"astar\",\"estado\":\"encontrada\",\"ruta\":[[1,1],[2,2]],\"costo\":1.4142135623730951,\"version_mapa\":1,\"metricas\":{\"nodos_expandidos\":2,\"nodos_descubiertos\":5,\"max_frontera\":4,\"tiempo_ms\":0.025},\"traza\":[{\"tipo\":\"frontera\",\"posicion\":[1,1],\"g\":0,\"h\":1.4142135623730951,\"padre\":null,\"linea\":1}]}";

        [MenuItem("Arcadia/Validate/Navigation safety")]
        public static void Run()
        {
            assertions = 0;
            CheckCodec();
            CheckRoutes();
            CheckNavigator();
            Debug.Log("ARCADIA_NAVIGATION_CHECKS_PASS: " + assertions + " assertions (codec, API response, diagonal rules, current-cell movement, obstacles, pause, cancellation, reset).");
        }

        private static void CheckCodec()
        {
            CultureInfo previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = new CultureInfo("es-PE");
                RouteResult route = EngineClient.ParseRoute(FoundJson);
                Assert(route.Found && route.Route.Length == 2, "Real API response must decode.");
                Assert(route.Route[1] == new GridCell(2, 2), "Coordinates must retain row/column order.");
                Assert(Math.Abs(route.Cost.Value - Math.Sqrt(2)) < 1e-12, "Decimal cost must not depend on system culture.");
                Assert(route.Metrics.Expanded == 2 && route.Metrics.Milliseconds == 0.025, "Metrics must retain values.");
                Assert(route.Trace.Length == 1 && route.Trace[0].Position == new GridCell(1, 1), "Trace with nullable parent must decode.");
                string plan = FoundJson.Replace("\"algoritmo\":\"astar\"", "\"motivo\":\"obstaculos\",\"algoritmo\":\"dstar_lite\"").Replace("\"g\":0", "\"g\":null");
                string sessionJson = "{\"id\":\"demo\",\"guia\":\"dstar_lite\",\"posicion\":[1,1],\"destino\":[2,2],\"bloqueadas\":[],\"ruta_restante\":[[1,1],[2,2]],\"vigentes\":{\"dstar_lite\":" + plan + "},\"nuevas\":[" + plan + "]}";
                SessionState session = EngineClient.ParseSession(sessionJson);
                Assert(double.IsPositiveInfinity(session.NewPlans[0].Result.Trace[0].G), "Null g represents an invalidated cell.");
                Assert(session.Remaining[0] == session.Position && session.Current[session.Guide].Reason == "obstaculos", "Guide and repaired route must decode.");
                string absent = FoundJson.Replace("\"encontrada\"", "\"sin_ruta\"").Replace("[[1,1],[2,2]]", "[]").Replace("\"costo\":1.4142135623730951", "\"costo\":null");
                RouteResult noRoute = EngineClient.ParseRoute(absent);
                Assert(!noRoute.Found && noRoute.Route.Length == 0 && !noRoute.Cost.HasValue, "No-route is a normal outcome.");
                Reject(() => EngineClient.ParseRoute(FoundJson + "junk"), "Trailing JSON must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"version_mapa\":1", "\"version_mapa\":1.5")), "Fractional integer metric must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("[[1,1],[2,2]]", "[[1,1],[2.5,2]]")), "Fractional coordinates must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"estado\":\"encontrada\"", "\"estado\":\"sin_ruta\"")), "No-route with populated path must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"costo\":1.4142135623730951", "\"costo\":null")), "Found path requires a cost.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"tiempo_ms\":0.025", "\"tiempo_ms\":-1")), "Negative duration must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"tiempo_ms\":0.025", "\"tiempo_ms\":1e999")), "Infinite number must fail.");
                Reject(() => EngineClient.ParseRoute(FoundJson.Replace("\"version_mapa\":1", "\"version_mapa\":1,\"version_mapa\":2")), "Duplicate properties must fail.");

                Type codec = typeof(EngineClient).Assembly.GetType("Arcadia.Navigation.JsonCodec", true);
                MethodInfo encode = codec.GetMethod("Stringify", BindingFlags.Static | BindingFlags.Public);
                MethodInfo decode = codec.GetMethod("Parse", BindingFlags.Static | BindingFlags.Public);
                var payload = new Dictionary<string, object> { { "inicio", new[] { 3, 8 } }, { "bloqueadas", new[] { new[] { 2, 7 } } }, { "traza", true }, { "label", "Luz \"Ámbar\"\n\\" }, { "cost", 1.5 } };
                string json = (string)encode.Invoke(null, new object[] { payload });
                var parsed = (Dictionary<string, object>)decode.Invoke(null, new object[] { json });
                var start = (List<object>)parsed["inicio"];
                Assert((double)start[0] == 3 && (double)start[1] == 8, "POST payload must preserve [row,column].");
                Assert((string)parsed["label"] == (string)payload["label"], "Escaping must round-trip Unicode, quotes and controls.");
                Assert((double)parsed["cost"] == 1.5 && (bool)parsed["traza"], "Writer must use JSON scalars and invariant decimals.");
                Reject(() => encode.Invoke(null, new object[] { double.NaN }), "Writer must reject NaN.");
                const string mapJson = "{\"nombre\":\"mini\",\"ancho\":3,\"alto\":2,\"filas\":[\".G@\",\"...\"]}";
                MapData map = EngineClient.ParseMap(mapJson);
                Assert(map.Width == 3 && map.Height == 2 && map.IsWalkable(new GridCell(0, 1)), "Bundled map and HTTP map must use the same parser.");
                Reject(() => EngineClient.ParseMap(mapJson.Replace("\"ancho\":3", "\"ancho\":4")), "Inconsistent row width must fail.");
                Reject(() => EngineClient.ParseMap(mapJson.Replace("\"alto\":2", "\"alto\":2.5")), "Fractional dimensions must fail.");
            }
            finally { CultureInfo.CurrentCulture = previous; }
        }

        private static void CheckRoutes()
        {
            MapData map = OpenMap();
            var blocked = new HashSet<GridCell>();
            GridCell a = new GridCell(1, 1), b = new GridCell(2, 2);
            Assert(RouteValidation.IsLegalStep(map, blocked, a, b), "Open diagonal should be legal.");
            blocked.Add(new GridCell(1, 2));
            Assert(!RouteValidation.IsLegalStep(map, blocked, a, b), "Diagonal cannot cut a dynamic corner.");
            blocked.Clear(); map.Rows[1] = "..@..";
            Assert(!RouteValidation.IsLegalStep(map, blocked, a, b), "Diagonal cannot cut a static corner.");
            map.Rows[1] = ".....";
            Assert(!RouteValidation.IsLegalStep(map, blocked, a, new GridCell(1, 3)), "A route cannot jump cells.");
            Assert(!RouteValidation.IsLegalStep(map, blocked, a, a), "Repeated path waypoint is invalid.");
            Assert(!RouteValidation.IsLegalStep(map, blocked, a, new GridCell(int.MinValue, int.MaxValue)), "Out-of-map coordinates must fail safely.");
            Assert(RouteValidation.IsLegal(map, blocked, a, b, EngineClient.ParseRoute(FoundJson)), "Valid server path should be accepted.");
            Assert(!RouteValidation.IsLegal(map, blocked, b, a, EngineClient.ParseRoute(FoundJson)), "Stale/reversed endpoints must be rejected.");
            var same = new RouteResult { Status = "encontrada", Route = new[] { a }, Cost = 0 };
            Assert(RouteValidation.IsLegal(map, blocked, a, a, same), "Already-at-destination path is valid.");
            blocked.Add(a);
            Assert(!RouteValidation.IsLegal(map, blocked, a, a, same), "Already-at-destination still requires free terrain.");
            map.Rows[0] = "G@TSW";
            Assert(map.IsWalkable(new GridCell(0, 0)) && !map.IsWalkable(new GridCell(0, 1)) && !map.IsWalkable(new GridCell(0, 2)) && !map.IsWalkable(new GridCell(0, 3)) && !map.IsWalkable(new GridCell(0, 4)), "Passability must match Python (. and G only).");
            map.Rows[0] = null;
            Assert(!map.IsWalkable(new GridCell(0, 0)), "Incomplete map row must fail closed.");
            Assert(!RouteValidation.IsLegalStep(null, null, a, b), "Missing map must fail closed.");
        }

        private static void CheckNavigator()
        {
            var owner = new GameObject("Navigation safety checks");
            try
            {
                EngineClient client = owner.AddComponent<EngineClient>();
                NpcNavigator npc = owner.AddComponent<NpcNavigator>();
                GridCell start = new GridCell(1, 1), diagonal = new GridCell(2, 2), goal = new GridCell(3, 3);
                npc.Initialize(client, OpenMap(), start);
                npc.Speed = 1;
                Assert(npc.CurrentCell == start && npc.State == NavigationState.Idle && !npc.HasDestination, "Initialization must put the NPC on a safe cell.");
                SeedRoute(npc, new[] { start, diagonal, goal });
                Advance(npc, 0.2f);
                Assert(npc.CurrentCell == start && Vector3.Distance(owner.transform.position, start.ToWorld()) > 0.19f, "CurrentCell must remain the last completed waypoint.");
                Assert(!npc.CanBlock(start) && !npc.CanBlock(diagonal) && !npc.CanBlock(goal), "Cannot place obstacles on the actor, in-flight endpoint or goal.");
                Assert(!npc.CanBlock(new GridCell(1, 2)) && !npc.CanBlock(new GridCell(2, 1)), "Protect both sides of the in-flight diagonal.");
                Vector3 beforePause = owner.transform.position;
                npc.SetPaused(true); Advance(npc, 10);
                Assert(npc.State == NavigationState.Paused && owner.transform.position == beforePause, "Pause must halt movement.");
                npc.SetPaused(false);
                Assert(npc.State == NavigationState.Moving, "Resume must restore movement state.");
                GridCell obstacle = new GridCell(0, 0);
                Assert(npc.SetSingleBlocked(obstacle, true), "A free cell away from the current edge may be blocked.");
                Assert(npc.State == NavigationState.ReturningToCell && npc.ActiveRoute.Count == 0, "Obstacle change invalidates the route before replanning.");
                float distanceBeforeReturn = Vector3.Distance(owner.transform.position, start.ToWorld());
                Advance(npc, 0.05f);
                Assert(Vector3.Distance(owner.transform.position, start.ToWorld()) < distanceBeforeReturn && npc.CurrentCell == start, "Return must follow the safe edge back to the current cell.");
                Assert(!npc.CanBlock(diagonal), "Returning edge remains protected after route invalidation.");
                Assert(!npc.SetBlocked(new[] { obstacle, start }) && npc.Blocked.Count == 1, "Invalid obstacle replacement must be atomic.");
                Assert(npc.ResetTo(start) && npc.State == NavigationState.Idle && !npc.HasDestination && npc.DistanceTravelled == 0 && npc.ActiveRoute.Count == 0, "Reset must cancel motion and clear counters and destination.");
                Assert(!npc.ResetTo(obstacle), "Reset cannot teleport onto an obstacle.");
                npc.SetBlocked(null);
                Assert(npc.Blocked.Count == 0, "Obstacles can be cleared.");

                SeedRoute(npc, new[] { start, diagonal });
                Advance(npc, 2f);
                Assert(npc.CurrentCell == diagonal && npc.State == NavigationState.Arrived, "A long frame must reach the final waypoint.");
                Assert(Math.Abs(npc.DistanceTravelled - Mathf.Sqrt(2)) < 0.00001f, "Diagonal movement uses physical distance rather than one cell per step.");

                npc.ResetTo(start);
                var path = new[] { start, new GridCell(1, 2), new GridCell(1, 3) };
                SeedRoute(npc, path); npc.Speed = 10;
                Action<GridCell> pauseAtCell = cell => npc.SetPaused(true);
                npc.CellReached += pauseAtCell;
                Advance(npc, 1f);
                Assert(npc.CurrentCell == path[1] && npc.State == NavigationState.Paused, "A pause requested by a waypoint callback must take effect in the same frame.");
                npc.CellReached -= pauseAtCell;
                npc.SetPaused(false); Advance(npc, 1f);
                Assert(npc.CurrentCell == path[2] && npc.State == NavigationState.Arrived, "Resume after waypoint pause must finish the path.");

                npc.ResetTo(start);
                var cancelled = new RequestCancellation(); cancelled.Cancel();
                IEnumerator query = client.Search("test", "astar", start, goal, null,
                    _ => throw new Exception("Cancelled request succeeded."), _ => throw new Exception("Cancelled request failed callback."), cancellation: cancelled);
                Assert(!query.MoveNext(), "Cancelled request must neither dispatch nor invoke a completion callback.");
                client.BaseUrl = "invalid-address";
                string failure = null;
                IEnumerator invalidUrl = client.CheckHealth(_ => throw new Exception("Invalid URL succeeded."), message => failure = message);
                Assert(!invalidUrl.MoveNext() && !string.IsNullOrEmpty(failure), "Malformed URL must produce an actionable error without a request.");
                var pending = new RequestCancellation();
                Set(npc, "pending", pending); Set(npc, "state", NavigationState.Planning);
                owner.SetActive(false);
                // Edit-mode objects do not receive runtime lifecycle callbacks.
                // Exercise the callback explicitly here; Play Mode covers dispatch.
                if (!Application.isPlaying)
                    typeof(NpcNavigator).GetMethod("OnDisable", BindingFlags.NonPublic | BindingFlags.Instance).Invoke(npc, null);
                Assert(pending.IsCancelled && npc.State == NavigationState.Idle, "Disabling a planning NPC must cancel the request and clear planning state.");
                npc.ResetTo(start);
                Assert(npc.LastError == "" && npc.LastResult == null && npc.ReplanCount == 0, "Reset must clear prior request outcome.");
            }
            finally { UnityEngine.Object.DestroyImmediate(owner); }
        }

        private static MapData OpenMap() => new MapData { Name = "checks", Width = 5, Height = 5, Rows = new[] { ".....", ".....", ".....", ".....", "....." } };

        // Seed an already-validated response; production route calculation remains exclusively HTTP/Python.
        // Reflection keeps test-only mutation and deterministic stepping out of the game's public API.
        private static void SeedRoute(NpcNavigator npc, GridCell[] route)
        {
            Set(npc, "route", route); Set(npc, "nextIndex", 1); Set(npc, "state", NavigationState.Moving);
            Set(npc, "<Destination>k__BackingField", route[route.Length - 1]);
            Set(npc, "<HasDestination>k__BackingField", true);
        }
        private static void Set(object target, string field, object value) => target.GetType().GetField(field, BindingFlags.NonPublic | BindingFlags.Instance).SetValue(target, value);
        private static void Advance(NpcNavigator npc, float seconds) => typeof(NpcNavigator).GetMethod("Advance", BindingFlags.NonPublic | BindingFlags.Instance).Invoke(npc, new object[] { seconds });
        private static void Assert(bool condition, string message)
        {
            if (!condition) throw new Exception("Navigation check failed: " + message);
            assertions++;
        }
        private static void Reject(Action action, string message)
        {
            try { action(); }
            catch (Exception error) when (error is FormatException || error is OverflowException || error is ArgumentException || (error is TargetInvocationException invocation && (invocation.InnerException is FormatException || invocation.InnerException is ArgumentException)))
            { assertions++; return; }
            throw new Exception("Navigation check failed: " + message);
        }
    }
}
