using System;
using System.Collections.Generic;
using UnityEngine;

namespace Arcadia.Navigation
{
    /// <summary>The API always uses [row,column], never [x,z].</summary>
    [Serializable]
    public struct GridCell : IEquatable<GridCell>
    {
        public int Row;
        public int Column;
        public GridCell(int row, int column) { Row = row; Column = column; }
        public Vector3 ToWorld(float y = 0f) => new Vector3(Column, y, Row);
        public static GridCell FromWorld(Vector3 position) => new GridCell(Mathf.RoundToInt(position.z), Mathf.RoundToInt(position.x));
        public bool Equals(GridCell other) => Row == other.Row && Column == other.Column;
        public override bool Equals(object obj) => obj is GridCell other && Equals(other);
        public override int GetHashCode() { unchecked { return (Row * 397) ^ Column; } }
        public static bool operator ==(GridCell a, GridCell b) => a.Equals(b);
        public static bool operator !=(GridCell a, GridCell b) => !a.Equals(b);
        public override string ToString() => "(" + Row + ", " + Column + ")";
    }

    [Serializable]
    public sealed class MapSummary
    {
        public string Name;
        public int Width, Height, Vertices, Scenarios;
    }

    [Serializable]
    public sealed class MapData
    {
        public string Name;
        public int Width, Height;
        public string[] Rows;
        public bool Contains(GridCell cell) => cell.Row >= 0 && cell.Row < Height && cell.Column >= 0 && cell.Column < Width;
        public bool IsWalkable(GridCell cell)
        {
            if (!Contains(cell) || Rows == null || cell.Row >= Rows.Length || Rows[cell.Row] == null || cell.Column >= Rows[cell.Row].Length) return false;
            char terrain = Rows[cell.Row][cell.Column];
            return terrain == '.' || terrain == 'G';
        }
    }

    [Serializable]
    public sealed class ScenarioData
    {
        public int Index, Bucket;
        public GridCell Start, Goal;
        public double OptimalCost;
    }

    [Serializable]
    public sealed class ScenarioPage
    {
        public string Map;
        public int Total, From, Limit;
        public ScenarioData[] Scenarios;
    }

    [Serializable]
    public sealed class SearchMetrics
    {
        public int Expanded, Discovered, MaxFrontier;
        public double Milliseconds;
    }

    [Serializable]
    public sealed class SearchEvent
    {
        public string Type;
        public GridCell Position;
        public double G, H;
        public int Line;
    }

    [Serializable]
    public sealed class RouteResult
    {
        public string Algorithm, Status;
        public GridCell[] Route = Array.Empty<GridCell>();
        public double? Cost;
        public int MapVersion;
        public SearchMetrics Metrics = new SearchMetrics();
        public SearchEvent[] Trace = Array.Empty<SearchEvent>();
        public bool Found => Status == "encontrada";
    }

    public enum NavigationState { Idle, Planning, Moving, ReturningToCell, Paused, Arrived, NoRoute, Error }

    /// <summary>Checks the server's result against the displayed grid; this does not search for routes.</summary>
    public static class RouteValidation
    {
        public static bool IsLegalStep(MapData map, ISet<GridCell> blocked, GridCell from, GridCell to)
        {
            if (map == null) return false;
            bool Walkable(GridCell p) => map.IsWalkable(p) && (blocked == null || !blocked.Contains(p));
            if (!Walkable(from) || !Walkable(to)) return false;
            int dr = Math.Abs(to.Row - from.Row), dc = Math.Abs(to.Column - from.Column);
            if (dr > 1 || dc > 1 || dr + dc == 0) return false;
            return dr == 0 || dc == 0 || (Walkable(new GridCell(from.Row, to.Column)) && Walkable(new GridCell(to.Row, from.Column)));
        }

        public static bool IsLegal(MapData map, ISet<GridCell> blocked, GridCell start, GridCell goal, RouteResult result)
        {
            if (map == null || result == null || !result.Found || result.Route == null || result.Route.Length == 0) return false;
            if (result.Route[0] != start || result.Route[result.Route.Length - 1] != goal) return false;
            if (!map.IsWalkable(start) || (blocked != null && blocked.Contains(start))) return false;
            for (int i = 1; i < result.Route.Length; i++)
                if (!IsLegalStep(map, blocked, result.Route[i - 1], result.Route[i])) return false;
            return true;
        }
    }
}
