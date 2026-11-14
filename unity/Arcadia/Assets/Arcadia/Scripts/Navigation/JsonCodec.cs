using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Arcadia.Navigation
{
    // Small JSON reader for nested numeric arrays unsupported by JsonUtility.
    // No runtime package, reflection or dynamic-code dependency is required.
    internal static class JsonCodec
    {
        public static object Parse(string text)
        {
            var reader = new Reader(text ?? throw new ArgumentNullException(nameof(text)));
            object value = reader.Value(0);
            reader.Space();
            if (!reader.AtEnd) throw new FormatException("Trailing data in JSON response.");
            return value;
        }

        public static string Stringify(object value)
        {
            var output = new StringBuilder();
            Write(output, value);
            return output.ToString();
        }

        private static void Write(StringBuilder output, object value)
        {
            if (value == null) { output.Append("null"); return; }
            if (value is string text) { Quote(output, text); return; }
            if (value is bool boolean) { output.Append(boolean ? "true" : "false"); return; }
            if (value is IDictionary dictionary)
            {
                output.Append('{'); bool first = true;
                foreach (DictionaryEntry item in dictionary)
                {
                    if (!first) output.Append(','); first = false;
                    Quote(output, Convert.ToString(item.Key, CultureInfo.InvariantCulture)); output.Append(':'); Write(output, item.Value);
                }
                output.Append('}'); return;
            }
            if (value is IEnumerable enumerable)
            {
                output.Append('['); bool first = true;
                foreach (object item in enumerable) { if (!first) output.Append(','); first = false; Write(output, item); }
                output.Append(']'); return;
            }
            if (value is double number && (double.IsNaN(number) || double.IsInfinity(number)))
                throw new ArgumentException("JSON cannot represent non-finite numbers.");
            if (value is float single && (float.IsNaN(single) || float.IsInfinity(single)))
                throw new ArgumentException("JSON cannot represent non-finite numbers.");
            if (!(value is byte || value is sbyte || value is short || value is ushort || value is int || value is uint
                || value is long || value is ulong || value is float || value is double || value is decimal))
                throw new ArgumentException("Unsupported JSON value: " + value.GetType().Name);
            output.Append(Convert.ToString(value, CultureInfo.InvariantCulture));
        }

        private static void Quote(StringBuilder output, string value)
        {
            output.Append('"');
            foreach (char c in value)
            {
                switch (c)
                {
                    case '"': output.Append("\\\""); break;
                    case '\\': output.Append("\\\\"); break;
                    case '\n': output.Append("\\n"); break;
                    case '\r': output.Append("\\r"); break;
                    case '\t': output.Append("\\t"); break;
                    default:
                        if (c < 32) output.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                        else output.Append(c);
                        break;
                }
            }
            output.Append('"');
        }

        private sealed class Reader
        {
            private readonly string text;
            private int cursor;
            public Reader(string text) { this.text = text; }
            public bool AtEnd => cursor >= text.Length;
            public void Space() { while (!AtEnd && (text[cursor] == ' ' || text[cursor] == '\t' || text[cursor] == '\r' || text[cursor] == '\n')) cursor++; }
            private static bool Digit(char c) => c >= '0' && c <= '9';
            private char Take() { if (AtEnd) throw new FormatException("Unexpected end of JSON."); return text[cursor++]; }
            private bool Consume(char value) { Space(); if (!AtEnd && text[cursor] == value) { cursor++; return true; } return false; }
            private void Expect(char value) { if (!Consume(value)) throw new FormatException("Expected '" + value + "' in JSON."); }
            public object Value(int depth)
            {
                if (depth > 128) throw new FormatException("JSON nesting too deep.");
                Space(); if (AtEnd) throw new FormatException("Empty JSON response.");
                switch (text[cursor])
                {
                    case '{':
                        cursor++; var obj = new Dictionary<string, object>();
                        if (Consume('}')) return obj;
                        do
                        {
                            Space(); string key = ReadString(); Expect(':');
                            if (obj.ContainsKey(key)) throw new FormatException("Duplicate JSON property: " + key);
                            obj.Add(key, Value(depth + 1));
                        } while (Consume(','));
                        Expect('}'); return obj;
                    case '[':
                        cursor++; var array = new List<object>();
                        if (Consume(']')) return array;
                        do { array.Add(Value(depth + 1)); } while (Consume(','));
                        Expect(']'); return array;
                    case '"': return ReadString();
                    case 't': Literal("true"); return true;
                    case 'f': Literal("false"); return false;
                    case 'n': Literal("null"); return null;
                    default: return Number();
                }
            }
            private void Literal(string word)
            {
                for (int i = 0; i < word.Length; i++) if (Take() != word[i]) throw new FormatException("Invalid JSON literal.");
            }
            private string ReadString()
            {
                if (Take() != '"') throw new FormatException("Expected JSON string.");
                var result = new StringBuilder();
                while (true)
                {
                    char c = Take();
                    if (c == '"') return result.ToString();
                    if (c < 32) throw new FormatException("Invalid control character in JSON.");
                    if (c != '\\') { result.Append(c); continue; }
                    switch (Take())
                    {
                        case '"': result.Append('"'); break;
                        case '\\': result.Append('\\'); break;
                        case '/': result.Append('/'); break;
                        case 'b': result.Append('\b'); break;
                        case 'f': result.Append('\f'); break;
                        case 'n': result.Append('\n'); break;
                        case 'r': result.Append('\r'); break;
                        case 't': result.Append('\t'); break;
                        case 'u':
                            if (cursor + 4 > text.Length) throw new FormatException("Truncated Unicode escape.");
                            result.Append((char)int.Parse(text.Substring(cursor, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture)); cursor += 4; break;
                        default: throw new FormatException("Invalid JSON escape.");
                    }
                }
            }
            private double Number()
            {
                int start = cursor;
                if (!AtEnd && text[cursor] == '-') cursor++;
                if (AtEnd || !Digit(text[cursor])) throw new FormatException("Invalid JSON number.");
                if (text[cursor] == '0') cursor++;
                else while (!AtEnd && Digit(text[cursor])) cursor++;
                if (!AtEnd && text[cursor] == '.')
                {
                    cursor++; int fraction = cursor;
                    while (!AtEnd && Digit(text[cursor])) cursor++;
                    if (cursor == fraction) throw new FormatException("Invalid fraction.");
                }
                if (!AtEnd && (text[cursor] == 'e' || text[cursor] == 'E'))
                {
                    cursor++; if (!AtEnd && (text[cursor] == '+' || text[cursor] == '-')) cursor++;
                    int exponent = cursor; while (!AtEnd && Digit(text[cursor])) cursor++;
                    if (cursor == exponent) throw new FormatException("Invalid exponent.");
                }
                double value = double.Parse(text.Substring(start, cursor - start), CultureInfo.InvariantCulture);
                if (double.IsNaN(value) || double.IsInfinity(value)) throw new FormatException("Non-finite JSON number.");
                return value;
            }
        }
    }
}
