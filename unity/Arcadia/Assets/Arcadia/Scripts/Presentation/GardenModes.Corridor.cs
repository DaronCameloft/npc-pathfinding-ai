using System.Collections;
using System.Linq;
using UnityEngine;

namespace Arcadia
{
    public sealed partial class GardenModes
    {
        IEnumerator ShowCorridor()
        {
            var data=Corridor;
            int top=data.zona[0],left=data.zona[1],bottom=data.zona[2],right=data.zona[3];
            Vector3 center=new Vector3((left+right)*.5f,0,(top+bottom)*.5f);
            Frame(center,80);
            var corners=new[]{new Vector3(left-.5f,.24f,top-.5f), new Vector3(right+.5f,.24f,top-.5f),
                new Vector3(right+.5f,.24f,bottom+.5f),new Vector3(left-.5f,.24f,bottom+.5f)};
            Line("Zona",corners,Mint,.16f).loop=true;
            Shade(0,0,game.Map.Width,top);
            Shade(0,bottom+1,game.Map.Width,game.Map.Height-bottom-1);
            Shade(0,top,left,bottom-top+1);
            Shade(right+1,top,game.Map.Width-right-1,bottom-top+1);
            foreach(var cell in data.entradas)Shape("Entrada",PrimitiveType.Cube,cell.ToWorld(.07f),new Vector3(.94f,.1f,.65f),Mint);
            foreach(var cell in data.salidas)Shape("Salida",PrimitiveType.Cube,cell.ToWorld(.07f),new Vector3(.94f,.1f,.65f),Amber);
            if(!Closed)cut=data.corte;
            foreach(var cell in cut)Shape(Closed?"Barrera del corte":"Runa del corte",PrimitiveType.Cube,
                cell.ToWorld(Closed?.9f:.14f),new Vector3(.91f,Closed?1.8f:.22f,.91f),Red,Closed);
            for(int i=0;i<data.aumentos.Length;i++)
            {
                var step=data.aumentos[i];
                var line=Line("Aumento",step.celdas.Select(c=>c.ToWorld(.29f)),Amber,.23f);
                Status=$"Aumento {i+1} de {data.aumentos.Length}    ·    Flujo acumulado {step.flujo}";
                yield return new WaitForSeconds(1);
                Destroy(line.gameObject);
            }
            var actors=new Transform[data.caminos.Length];
            for(int i=0;i<actors.Length;i++)
            {
                var lane=data.caminos[i];var color=LaneColors[i%LaneColors.Length];
                Line("Camino disjunto",lane.Select(c=>c.ToWorld(.19f)),color,.28f);
                actors[i]=Guardian("Guardián de pasillo "+(i+1),lane[0].ToWorld(),color,1.45f);
            }
            Ready=true;
            Status=$"{data.flujo_maximo} NPC a la vez    ·    Corte de {cut.Length} celdas\n{data.celdas} celdas libres    ·    {data.entradas.Length} entradas y {data.salidas.Length} salidas    ·    {data.tiempo_ms:0.0} ms";
            if(actors.Length==0)yield break;
            float progress=0;int length=data.caminos.Max(lane=>lane.Length);
            while(progress<length-1)
            {
                progress+=Time.deltaTime*5;
                for(int i=0;i<actors.Length;i++)
                {
                    var lane=data.caminos[i];
                    int j=Mathf.Min((int)progress,lane.Length-1);
                    var from=lane[j].ToWorld();var to=lane[Mathf.Min(j+1,lane.Length-1)].ToWorld();
                    actors[i].position=Vector3.Lerp(from,to,progress-j);
                    if(to!=from)actors[i].rotation=Quaternion.LookRotation(to-from);
                }
                yield return null;
            }
        }

        void Shade(float x,float z,float width,float depth)
        {
            if(width<=0 || depth<=0)return;
            var tint=new Color(.03f,.09f,.08f,.28f);
            var panel=Shape("Exterior de la zona",PrimitiveType.Cube,new Vector3(x+(width-1)/2,.09f,z+(depth-1)/2),
                new Vector3(width,.01f,depth),tint);
            if(!veil)veil=new Material(UnityEngine.UI.Graphic.defaultGraphicMaterial){color=tint};
            var renderer=panel.GetComponent<Renderer>();
            renderer.sharedMaterial=veil;
            renderer.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
        }
    }
}
