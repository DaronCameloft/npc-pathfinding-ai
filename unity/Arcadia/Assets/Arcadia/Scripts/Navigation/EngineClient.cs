using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace Arcadia.Navigation
{
    /// <summary>Each operation owns a token; cancelling it cannot cancel a newer request.</summary>
    public sealed class RequestCancellation
    {
        public bool IsCancelled { get; private set; }
        private UnityWebRequest request;
        public void Cancel()
        {
            IsCancelled = true;
            // The owner may have been destroyed before its coroutine's finally block.
            try { request?.Abort(); } catch (ObjectDisposedException) { request = null; }
        }
        internal void Attach(UnityWebRequest value) { request = value; if (IsCancelled) request.Abort(); }
        internal void Detach(UnityWebRequest value) { if (ReferenceEquals(request, value)) request = null; }
    }

    public sealed partial class EngineClient : MonoBehaviour
    {
        public string BaseUrl = "http://127.0.0.1:8000";
        [Range(1, 120)] public int RequestTimeoutSeconds = 30;
        private readonly HashSet<UnityWebRequest> activeRequests = new HashSet<UnityWebRequest>();
        private bool shuttingDown;

        public IEnumerator CheckHealth(Action<string> success, Action<string> failure, RequestCancellation cancellation = null)
        {
            return Send("GET", "/health", null, raw => Decode(raw, x => Text(Object(x), "version"), success, failure), failure, cancellation);
        }

        public IEnumerator GetMaps(Action<MapSummary[]> success, Action<string> failure, RequestCancellation cancellation = null)
        {
            return Send("GET", "/mapas", null, raw => Decode(raw, ReadMaps, success, failure), failure, cancellation);
        }

        public IEnumerator GetMap(string name, Action<MapData> success, Action<string> failure, RequestCancellation cancellation = null)
        {
            return Send("GET", "/mapas/" + Uri.EscapeDataString(name), null,
                raw => Decode(raw, ReadMap, success, failure), failure, cancellation);
        }

        public IEnumerator GetScenarios(string map, int index, int limit, Action<ScenarioPage> success, Action<string> failure, RequestCancellation cancellation = null)
        {
            string path = "/mapas/" + Uri.EscapeDataString(map) + "/escenarios?desde=" + Math.Max(0, index) + "&limite=" + Mathf.Clamp(limit, 1, 1000);
            return Send("GET", path, null, raw => Decode(raw, ReadScenarios, success, failure), failure, cancellation);
        }

        public IEnumerator Search(string map, string algorithm, GridCell start, GridCell goal,
            IEnumerable<GridCell> blocked, Action<RouteResult> success, Action<string> failure,
            bool trace = false, RequestCancellation cancellation = null)
        {
            var cells = new List<object>();
            if (blocked != null) foreach (GridCell cell in blocked) cells.Add(new[] { cell.Row, cell.Column });
            var payload = new Dictionary<string, object>
            {
                { "mapa", map }, { "algoritmo", algorithm },
                { "inicio", new[] { start.Row, start.Column } }, { "destino", new[] { goal.Row, goal.Column } },
                { "bloqueadas", cells }, { "traza", trace }
            };
            return Send("POST", "/buscar", JsonCodec.Stringify(payload),
                raw => Decode(raw, ReadRoute, success, failure), failure, cancellation);
        }

        static int[] Pair(GridCell cell) => new[] { cell.Row, cell.Column };
        static int[][] Pairs(IEnumerable<GridCell> cells) => new List<GridCell>(cells).ConvertAll(Pair).ToArray();
        static string SessionPath(string id) => "/sesiones/" + Uri.EscapeDataString(id);

        private IEnumerator SessionRequest(string method, string path, object body, Action<SessionState> success,
            Action<string> failure, RequestCancellation token)
            => Send(method, path, body == null ? null : JsonCodec.Stringify(body),
                raw => Decode(raw, ReadSession, success, failure), failure, token);

        public IEnumerator OpenSession(string map, string guide, GridCell start, GridCell goal, IEnumerable<GridCell> blocked,
            bool trace, Action<SessionState> success, Action<string> failure, RequestCancellation token = null)
        {
            var body = new Dictionary<string, object> {
                { "mapa", map }, { "inicio", Pair(start) }, { "destino", Pair(goal) }, { "bloqueadas", Pairs(blocked) },
                { "algoritmos", new[] { guide, guide == "astar" ? "dstar_lite" : "astar" } }, { "traza", trace }
            };
            return SessionRequest("POST", "/sesiones", body, success, failure, token);
        }

        public IEnumerator Advance(string id, int steps, Action<SessionState> success, Action<string> failure, RequestCancellation token = null)
            => SessionRequest("POST", SessionPath(id) + "/avanzar", new Dictionary<string, object> { { "pasos", steps } }, success, failure, token);

        public IEnumerator ChangeObstacles(string id, IEnumerable<GridCell> block, IEnumerable<GridCell> free, bool trace,
            Action<SessionState> success, Action<string> failure, RequestCancellation token = null)
            => SessionRequest("POST", SessionPath(id) + "/obstaculos", new Dictionary<string, object> {
                { "bloquear", Pairs(block) }, { "liberar", Pairs(free) }, { "traza", trace }
            }, success, failure, token);

        public IEnumerator GetSession(string id, Action<SessionState> success, Action<string> failure, RequestCancellation token = null)
            => SessionRequest("GET", SessionPath(id), null, success, failure, token);

        public IEnumerator CloseSession(string id, Action<string> failure = null, RequestCancellation token = null)
            => Send("DELETE", SessionPath(id), null, null, failure, token);

        public static SessionState ParseSession(string json) => ReadSession(JsonCodec.Parse(json));

        static Planning ReadPlanning(object value) => new Planning { Reason = Text(Object(value), "motivo"), Result = ReadRoute(value) };

        static SessionState ReadSession(object value)
        {
            var entry = Object(value);
            var state = new SessionState {
                Id = Text(entry, "id"), Guide = Text(entry, "guia"), Position = Cell(entry["posicion"]), Goal = Cell(entry["destino"]),
                Remaining = Array(entry["ruta_restante"]).ConvertAll(Cell).ToArray(),
                Blocked = Array(entry["bloqueadas"]).ConvertAll(Cell).ToArray(),
                NewPlans = Array(entry["nuevas"]).ConvertAll(ReadPlanning).ToArray()
            };
            foreach (var pair in Object(entry["vigentes"])) state.Current.Add(pair.Key, ReadPlanning(pair.Value));
            if (!state.Current.ContainsKey(state.Guide)) throw new FormatException("Missing guide plan.");
            return state;
        }

        private IEnumerator Send(string method, string path, string json, Action<string> success, Action<string> failure, RequestCancellation cancellation)
        {
            if (cancellation != null && cancellation.IsCancelled) yield break;
            if (shuttingDown) { failure?.Invoke("El cliente del motor ya no está disponible."); yield break; }
            string url = (BaseUrl ?? "").TrimEnd('/') + path;
            if (!Uri.TryCreate(url, UriKind.Absolute, out Uri endpoint) || (endpoint.Scheme != "http" && endpoint.Scheme != "https"))
            { failure?.Invoke("La dirección del motor debe ser una URL HTTP o HTTPS válida."); yield break; }
            var request = new UnityWebRequest(endpoint.AbsoluteUri, method);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.timeout = Mathf.Clamp(RequestTimeoutSeconds, 1, 120);
            request.SetRequestHeader("Accept", "application/json");
            if (json != null)
            {
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                request.SetRequestHeader("Content-Type", "application/json");
            }
            activeRequests.Add(request);
            cancellation?.Attach(request);
            try
            {
                yield return request.SendWebRequest();
                if (shuttingDown || (cancellation != null && cancellation.IsCancelled)) yield break;
                if (request.result != UnityWebRequest.Result.Success)
                {
                    string detail = request.downloadHandler?.text;
                    if (string.IsNullOrWhiteSpace(detail)) detail = request.error;
                    if (detail != null && detail.Length > 350) detail = detail.Substring(0, 350);
                    failure?.Invoke(request.responseCode == 0
                        ? "No se pudo conectar al motor Python en " + BaseUrl + ". " + detail
                        : "Motor HTTP " + request.responseCode + ": " + detail);
                    yield break;
                }
                success?.Invoke(request.downloadHandler.text);
            }
            finally
            {
                cancellation?.Detach(request);
                if (activeRequests.Remove(request)) request.Dispose();
            }
        }

        private void OnDestroy()
        {
            shuttingDown = true;
            foreach (UnityWebRequest request in activeRequests) { request.Abort(); request.Dispose(); }
            activeRequests.Clear();
        }

        private static void Decode<T>(string raw, Func<object, T> read, Action<T> success, Action<string> failure)
        {
            T result;
            try { result = read(JsonCodec.Parse(raw)); }
            catch (Exception error) when (error is FormatException || error is InvalidCastException || error is OverflowException || error is KeyNotFoundException)
            { failure?.Invoke("Respuesta del motor no válida: " + error.Message); return; }
            success?.Invoke(result);
        }

        private static Dictionary<string, object> Object(object value) => value as Dictionary<string, object> ?? throw new FormatException("Expected a JSON object.");
        private static List<object> Array(object value) => value as List<object> ?? throw new FormatException("Expected a JSON array.");
        private static string Text(Dictionary<string, object> value, string key) => value[key] as string ?? throw new FormatException("Expected string: " + key);
        private static double Number(Dictionary<string, object> value, string key) => value[key] is double number ? number : throw new FormatException("Expected number: " + key);
        private static int Integer(Dictionary<string, object> value, string key)
        {
            double number = Number(value, key);
            if (number != Math.Truncate(number)) throw new FormatException("Expected integer: " + key);
            return checked((int)number);
        }
        private static GridCell Cell(object value)
        {
            List<object> pair = Array(value);
            if (pair.Count != 2 || !(pair[0] is double row) || !(pair[1] is double column) || row != Math.Truncate(row) || column != Math.Truncate(column))
                throw new FormatException("Expected [row,column] integer pair.");
            return new GridCell(checked((int)row), checked((int)column));
        }
        private static MapSummary[] ReadMaps(object value)
        {
            List<object> list = Array(value); var result = new MapSummary[list.Count];
            for (int i = 0; i < result.Length; i++)
            {
                var entry = Object(list[i]);
                result[i] = new MapSummary { Name = Text(entry, "nombre"), Width = Integer(entry, "ancho"), Height = Integer(entry, "alto"), Vertices = Integer(entry, "vertices"), Scenarios = Integer(entry, "escenarios") };
            }
            return result;
        }
        private static MapData ReadMap(object value)
        {
            var entry = Object(value); List<object> rows = Array(entry["filas"]);
            var result = new MapData { Name = Text(entry, "nombre"), Width = Integer(entry, "ancho"), Height = Integer(entry, "alto"), Rows = new string[rows.Count] };
            if (result.Width <= 0 || result.Height <= 0 || result.Height != rows.Count) throw new FormatException("Inconsistent map dimensions.");
            for (int i = 0; i < rows.Count; i++)
            {
                result.Rows[i] = rows[i] as string;
                if (result.Rows[i] == null || result.Rows[i].Length != result.Width) throw new FormatException("Inconsistent map row width.");
            }
            return result;
        }
        private static ScenarioPage ReadScenarios(object value)
        {
            var entry = Object(value); List<object> scenarios = Array(entry["escenarios"]);
            var result = new ScenarioPage { Map = Text(entry, "mapa"), Total = Integer(entry, "total"), From = Integer(entry, "desde"), Limit = Integer(entry, "limite"), Scenarios = new ScenarioData[scenarios.Count] };
            for (int i = 0; i < scenarios.Count; i++)
            {
                var scenario = Object(scenarios[i]);
                result.Scenarios[i] = new ScenarioData { Index = Integer(scenario, "indice"), Bucket = Integer(scenario, "bucket"), Start = Cell(scenario["inicio"]), Goal = Cell(scenario["destino"]), OptimalCost = Number(scenario, "optimo") };
            }
            return result;
        }
        public static MapData ParseMap(string json) => ReadMap(JsonCodec.Parse(json));
        public static RouteResult ParseRoute(string json) => ReadRoute(JsonCodec.Parse(json));
        private static RouteResult ReadRoute(object value)
        {
            var entry = Object(value); List<object> cells = Array(entry["ruta"]); var metrics = Object(entry["metricas"]);
            var result = new RouteResult
            {
                Algorithm = Text(entry, "algoritmo"), Status = Text(entry, "estado"), MapVersion = Integer(entry, "version_mapa"),
                Cost = entry["costo"] == null ? (double?)null : Number(entry, "costo"), Route = new GridCell[cells.Count],
                Metrics = new SearchMetrics { Expanded = Integer(metrics, "nodos_expandidos"), Discovered = Integer(metrics, "nodos_descubiertos"), MaxFrontier = Integer(metrics, "max_frontera"), Milliseconds = Number(metrics, "tiempo_ms") }
            };
            if (result.Status != "encontrada" && result.Status != "sin_ruta") throw new FormatException("Unknown route status.");
            if (result.MapVersion < 0 || result.Metrics.Expanded < 0 || result.Metrics.Discovered < 0 || result.Metrics.MaxFrontier < 0 || result.Metrics.Milliseconds < 0)
                throw new FormatException("Negative search metrics.");
            if (result.Found ? (!result.Cost.HasValue || result.Cost.Value < 0 || cells.Count == 0) : (result.Cost.HasValue || cells.Count != 0))
                throw new FormatException("Route status, cost and cells disagree.");
            for (int i = 0; i < cells.Count; i++) result.Route[i] = Cell(cells[i]);
            if (entry.TryGetValue("traza", out object rawTrace) && rawTrace != null)
            {
                List<object> trace = Array(rawTrace); result.Trace = new SearchEvent[trace.Count];
                for (int i = 0; i < trace.Count; i++)
                {
                    var item = Object(trace[i]);
                    result.Trace[i] = new SearchEvent { Type = Text(item, "tipo"), Position = Cell(item["posicion"]), G = item["g"] == null ? double.PositiveInfinity : Number(item, "g"), H = Number(item, "h"), Line = Integer(item, "linea") };
                }
            }
            return result;
        }
    }
}
