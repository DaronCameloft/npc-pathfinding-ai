using System;
using System.Collections.Generic;
using UnityEngine;

namespace Arcadia.Navigation
{
    /// <summary>
    /// Follows server-supplied grid edges. Obstacles and destination changes cancel
    /// old requests, return to the last completed cell, then replan from that cell.
    /// No navigation algorithm runs in Unity.
    /// </summary>
    public sealed class NpcNavigator : MonoBehaviour
    {
        [Min(0.1f)] public float Speed = 3.5f;
        [Min(1f)] public float TurnSpeed = 540f;
        public float GroundHeight = 0f;
        public bool RequestTrace;
        public Transform VisualRoot;
        public Func<GridCell, Vector3> CellToWorld;

        public EngineClient Client { get; private set; }
        public MapData Map { get; private set; }
        public GridCell CurrentCell { get; private set; }
        public GridCell Destination { get; private set; }
        public bool HasDestination { get; private set; }
        public string Algorithm { get; private set; } = "astar";
        public NavigationState State => IsPaused ? NavigationState.Paused : state;
        public bool IsPaused { get; private set; }
        public bool IsMoving => !IsPaused && (state == NavigationState.Moving || state == NavigationState.ReturningToCell);
        public RouteResult LastResult { get; private set; }
        public IReadOnlyList<GridCell> ActiveRoute => route;
        public int RouteIndex => nextIndex;
        public IReadOnlyCollection<GridCell> Blocked => blocked;
        public int ReplanCount { get; private set; }
        public float DistanceTravelled { get; private set; }
        public string LastError { get; private set; } = "";

        public event Action<NavigationState> StateChanged;
        public event Action<RouteResult> RouteChanged;
        public event Action RouteInvalidated;
        public event Action<GridCell> CellReached;
        public event Action<string> Error;
        public event Action Arrived;

        private readonly HashSet<GridCell> blocked = new HashSet<GridCell>();
        private GridCell[] route = Array.Empty<GridCell>();
        private int nextIndex, requestGeneration;
        private NavigationState state = NavigationState.Idle;
        private RequestCancellation pending;
        private GridCell? returningEdgeEnd;
        private bool hasPlanned;

        public void Initialize(EngineClient client, MapData map, GridCell start, Transform visualRoot = null)
        {
            if (client == null || map == null) throw new ArgumentNullException(client == null ? nameof(client) : nameof(map));
            if (!map.IsWalkable(start)) throw new ArgumentException("NPC start must be walkable.", nameof(start));
            CancelPending();
            Client = client; Map = map;
            if (visualRoot != null) VisualRoot = visualRoot;
            blocked.Clear();
            ResetTo(start);
        }

        public Vector3 WorldPosition(GridCell cell) => CellToWorld != null ? CellToWorld(cell) : cell.ToWorld(GroundHeight);

        public bool ResetTo(GridCell cell)
        {
            if (Map == null || !Map.IsWalkable(cell) || blocked.Contains(cell)) return false;
            CancelPending();
            CurrentCell = Destination = cell;
            HasDestination = false;
            IsPaused = false;
            LastResult = null; LastError = "";
            ReplanCount = 0; DistanceTravelled = 0; hasPlanned = false;
            returningEdgeEnd = null;
            transform.position = WorldPosition(cell);
            ClearRoute();
            SetState(NavigationState.Idle);
            CellReached?.Invoke(cell);
            return true;
        }

        public bool GoTo(GridCell goal)
        {
            if (Map == null || Client == null || !Map.IsWalkable(goal) || blocked.Contains(goal)) return false;
            if (HasDestination && Destination == goal && state != NavigationState.Error && state != NavigationState.NoRoute && state != NavigationState.Idle) return true;
            Destination = goal; HasDestination = true;
            PrepareSearch();
            return true;
        }

        public void Replan()
        {
            if (HasDestination && Map != null && Client != null) PrepareSearch();
        }

        public void SetAlgorithm(string algorithm)
        {
            if (string.IsNullOrWhiteSpace(algorithm) || Algorithm == algorithm) return;
            Algorithm = algorithm;
            if (HasDestination) PrepareSearch();
        }

        public void SetPaused(bool value)
        {
            if (IsPaused == value) return;
            IsPaused = value;
            StateChanged?.Invoke(State);
        }

        /// <summary>Protects the occupied cell, destination and full in-progress edge.</summary>
        public bool CanBlock(GridCell cell)
        {
            if (Map == null || !Map.IsWalkable(cell) || cell == CurrentCell || (HasDestination && cell == Destination)) return false;
            GridCell? end = returningEdgeEnd;
            if (!end.HasValue && state == NavigationState.Moving && nextIndex < route.Length
                && Vector3.SqrMagnitude(transform.position - WorldPosition(CurrentCell)) > 0.000001f)
                end = route[nextIndex];
            if (!end.HasValue) return true;
            GridCell target = end.Value;
            if (cell == target) return false;
            if (target.Row != CurrentCell.Row && target.Column != CurrentCell.Column)
                return cell != new GridCell(CurrentCell.Row, target.Column) && cell != new GridCell(target.Row, CurrentCell.Column);
            return true;
        }

        /// <summary>Caller must update the rendered obstacle only after this returns true.</summary>
        public bool SetSingleBlocked(GridCell cell, bool isBlocked)
        {
            var replacement = new HashSet<GridCell>(blocked);
            if (isBlocked) replacement.Add(cell); else replacement.Remove(cell);
            return SetBlocked(replacement);
        }

        public bool SetBlocked(IEnumerable<GridCell> cells)
        {
            if (Map == null) return false;
            var replacement = cells == null ? new HashSet<GridCell>() : new HashSet<GridCell>(cells);
            foreach (GridCell cell in replacement)
                if (!Map.IsWalkable(cell) || (!blocked.Contains(cell) && !CanBlock(cell))) return false;
            if (blocked.SetEquals(replacement)) return true;
            blocked.Clear(); blocked.UnionWith(replacement);
            if (HasDestination) PrepareSearch();
            return true;
        }

        private void PrepareSearch()
        {
            CancelPending(); LastError = "";
            Vector3 safe = WorldPosition(CurrentCell);
            bool betweenCells = Vector3.SqrMagnitude(transform.position - safe) > 0.000001f;
            if (betweenCells && !returningEdgeEnd.HasValue && nextIndex < route.Length) returningEdgeEnd = route[nextIndex];
            ClearRoute();
            if (betweenCells) SetState(NavigationState.ReturningToCell);
            else { returningEdgeEnd = null; BeginSearch(); }
        }

        private void BeginSearch()
        {
            if (!HasDestination || Client == null) return;
            if (!isActiveAndEnabled) { SetState(NavigationState.Idle); return; }
            int generation = ++requestGeneration;
            var token = new RequestCancellation(); pending = token;
            GridCell start = CurrentCell, goal = Destination;
            var obstacleSnapshot = new HashSet<GridCell>(blocked);
            string selectedAlgorithm = Algorithm;
            if (hasPlanned) ReplanCount++;
            hasPlanned = true;
            SetState(NavigationState.Planning);
            if (generation != requestGeneration || token.IsCancelled) return;
            StartCoroutine(Client.Search(Map.Name, selectedAlgorithm, start, goal, obstacleSnapshot,
                result =>
                {
                    if (generation != requestGeneration || token.IsCancelled || this == null) return;
                    pending = null;
                    if (result.Algorithm != selectedAlgorithm)
                    { Fail("La respuesta corresponde a otro algoritmo."); return; }
                    if (!result.Found)
                    {
                        LastResult = result;
                        ClearRoute(); SetState(NavigationState.NoRoute); RouteChanged?.Invoke(result); return;
                    }
                    if (!RouteValidation.IsLegal(Map, obstacleSnapshot, start, goal, result))
                    { Fail("La ruta recibida no respeta el mapa y sus obstáculos."); return; }
                    LastResult = result;
                    route = result.Route;
                    nextIndex = 1;
                    SetState(route.Length > 1 ? NavigationState.Moving : NavigationState.Arrived);
                    if (generation != requestGeneration) return;
                    RouteChanged?.Invoke(result);
                    if (generation == requestGeneration && route.Length == 1) Arrived?.Invoke();
                },
                message => { if (generation == requestGeneration && !token.IsCancelled && this != null) { pending = null; Fail(message); } },
                RequestTrace, token));
        }

        private void Update() => Advance(Time.deltaTime);

        // Keep the distance budget deterministic so safety checks can cover long frames.
        private void Advance(float deltaTime)
        {
            if (IsPaused || Map == null || deltaTime <= 0f) return;
            if (state == NavigationState.ReturningToCell)
            {
                if (MoveToward(WorldPosition(CurrentCell), Mathf.Max(0.1f, Speed) * deltaTime, deltaTime))
                { returningEdgeEnd = null; BeginSearch(); }
                return;
            }
            if (state != NavigationState.Moving) return;
            float budget = Mathf.Max(0.1f, Speed) * deltaTime;
            // Spend distance, not one "step" per frame: diagonal speed stays identical.
            while (budget > 0f && nextIndex < route.Length)
            {
                GridCell next = route[nextIndex];
                if (!RouteValidation.IsLegalStep(Map, blocked, CurrentCell, next)) { PrepareSearch(); return; }
                Vector3 target = WorldPosition(next);
                float distance = Vector3.Distance(transform.position, target);
                bool reached = MoveToward(target, budget, deltaTime);
                budget = Mathf.Max(0f, budget - distance);
                if (!reached) break;
                CurrentCell = next; nextIndex++;
                CellReached?.Invoke(CurrentCell);
                // An event subscriber may request a new route/obstacle set.
                if (IsPaused || state != NavigationState.Moving || CurrentCell != next) return;
            }
            if (nextIndex >= route.Length && state == NavigationState.Moving)
            { SetState(NavigationState.Arrived); Arrived?.Invoke(); }
        }

        private bool MoveToward(Vector3 target, float distance, float deltaTime)
        {
            Vector3 before = transform.position;
            Vector3 facing = target - before; facing.y = 0f;
            Transform visual = VisualRoot != null ? VisualRoot : transform;
            if (facing.sqrMagnitude > 0.00001f)
                visual.rotation = Quaternion.RotateTowards(visual.rotation, Quaternion.LookRotation(facing), TurnSpeed * deltaTime);
            transform.position = Vector3.MoveTowards(before, target, distance);
            bool reached = Vector3.SqrMagnitude(transform.position - target) < 0.000001f;
            if (reached) transform.position = target;
            DistanceTravelled += Vector3.Distance(before, transform.position);
            return reached;
        }

        private void ClearRoute()
        {
            route = Array.Empty<GridCell>(); nextIndex = 0;
            RouteInvalidated?.Invoke();
        }
        private void CancelPending()
        {
            requestGeneration++;
            pending?.Cancel(); pending = null;
        }
        private void SetState(NavigationState next)
        {
            state = next;
            StateChanged?.Invoke(State);
        }
        private void Fail(string message)
        {
            LastError = message; ClearRoute(); SetState(NavigationState.Error); Error?.Invoke(message);
        }
        private void OnDisable()
        {
            CancelPending();
            if (state == NavigationState.Planning) SetState(NavigationState.Idle);
        }
        private void OnEnable()
        {
            // A disabled GameObject stops its coroutines; resume the cancelled query.
            if (HasDestination && state == NavigationState.Idle && Client != null && Map != null) PrepareSearch();
        }
        private void OnDestroy() => CancelPending();
    }
}
