using System;
using System.Collections;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Arcadia.Navigation
{
    // Field names mirror the Python wire contract. Coordinates retain row/column order.
    public sealed class AlgorithmInfo { public string clave, nombre, tecnica, complejidad, referencia, caso_de_uso; public AlgorithmLine[] pseudocodigo; }
    public sealed class AlgorithmLine { public int numero, nivel; public string texto; }
    public sealed class Aumento { public GridCell[] celdas; public int flujo; }
    public sealed class AnalisisPasillo
    {
        public int[] zona;
        public GridCell[] entradas, salidas, bloqueadas, corte;
        public int celdas, flujo_maximo;
        public double tiempo_ms;
        public GridCell[][] caminos;
        public Aumento[] aumentos;
    }
    public sealed class Tramo { public int desde, hasta; public double costo; public GridCell[] ruta; }
    public sealed class Decision { public int desde, hasta, linea; public double costo; public bool aceptada; }
    public sealed class RedPatrullaje
    {
        public GridCell[] puntos;
        public Tramo[] candidatas, arbol;
        public int[][] sin_ruta;
        public Decision[] decisiones;
        public double costo_arbol, costo_candidatas, tiempo_rutas_ms, tiempo_kruskal_ms;
        public int componentes;
    }
    public sealed class Objeto { public string nombre; public int peso, valor; }
    public sealed class Carga { public int[] elegidos; public int peso, valor; }
    public sealed class SeleccionBotin
    {
        public Objeto[] objetos;
        public int capacidad;
        public Carga optima, voraz;
        public int[][] tabla;
        public GridCell[] reconstruccion;
        public double tiempo_ms;
    }

    public sealed partial class EngineClient
    {
        sealed class CellReader : JsonConverter<GridCell>
        {
            public override bool CanWrite => false;
            public override void WriteJson(JsonWriter writer, GridCell value, JsonSerializer serializer) => throw new NotSupportedException();
            public override GridCell ReadJson(JsonReader reader, Type type, GridCell existing, bool hasExisting, JsonSerializer serializer)
            {
                var pair = JArray.Load(reader);
                if (pair.Count != 2 || pair[0].Type != JTokenType.Integer || pair[1].Type != JTokenType.Integer)
                    throw new JsonSerializationException("Se esperaba una celda [fila, columna].");
                return new GridCell((int)pair[0], (int)pair[1]);
            }
        }

        IEnumerator GraphRequest<T>(string path, object body, Action<T> success, Action<string> failure, RequestCancellation token)
        {
            return Send(body == null ? "GET" : "POST", path, body == null ? null : JsonConvert.SerializeObject(body), raw =>
            {
                T data;
                try { data = JsonConvert.DeserializeObject<T>(raw, new CellReader()); }
                catch (JsonException ex) { failure("Respuesta inválida del motor. " + ex.Message); return; }
                if (data == null) { failure("Respuesta vacía del motor."); return; }
                success(data);
            }, failure, token);
        }

        public IEnumerator GetCatalog(Action<AlgorithmInfo[]> success, Action<string> failure, RequestCancellation token)
            => GraphRequest("/complementarios", null, success, failure, token);
        public IEnumerator Corridor(string map, IEnumerable<GridCell> blocked, Action<AnalisisPasillo> success, Action<string> failure, RequestCancellation token)
            => GraphRequest("/pasillo", new { mapa=map, zona=new[]{24,156,71,203}, direccion="vertical", bloqueadas=Pairs(blocked) }, success, failure, token);
        public IEnumerator Patrol(string map, int seed, Action<RedPatrullaje> success, Action<string> failure, RequestCancellation token)
            => GraphRequest("/patrullaje", new { mapa=map, cantidad=7, semilla=seed }, success, failure, token);
        public IEnumerator Loot(int capacity, Action<SeleccionBotin> success, Action<string> failure, RequestCancellation token)
            => GraphRequest("/botin", new { capacidad=capacity }, success, failure, token);
    }
}
