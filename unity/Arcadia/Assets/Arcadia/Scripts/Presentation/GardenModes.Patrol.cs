using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Arcadia.Navigation;
using UnityEngine;

namespace Arcadia
{
    public sealed partial class GardenModes
    {
        Transform patrolActor;
        IEnumerator ShowPatrol()
        {
            var data=Patrol;
            var bounds=new Bounds(data.puntos[0].ToWorld(),Vector3.zero);
            foreach(var cell in data.puntos)bounds.Encapsulate(cell.ToWorld());
            float aspect=game.Rig.GetComponent<Camera>().aspect;
            Frame(bounds.center,Mathf.Max(bounds.size.z,bounds.size.x/aspect)*1.65f+12,80);
            for(int i=0;i<data.puntos.Length;i++)
            {
                var pillar=Shape("Farol P"+(i+1),PrimitiveType.Cylinder,data.puntos[i].ToWorld(1.5f),new Vector3(2,1.5f,2),Amber);
                Caption(pillar.transform,"P"+(i+1),.55f,4);
            }
            double total=0;
            foreach(var decision in data.decisiones)
            {
                var edge=data.candidatas.First(e=>e.desde==decision.desde && e.hasta==decision.hasta);
                var line=Line(decision.aceptada?"Tramo del árbol":"Ciclo",edge.ruta.Select(c=>c.ToWorld(.8f)),
                    decision.aceptada?Mint:Amber,1.1f);
                if(decision.aceptada)total+=edge.costo;
                Status=$"P{edge.desde+1} – P{edge.hasta+1}    ·    {(decision.aceptada?"Entra al árbol":"Ya conectados, cerraría un ciclo")}\nCosto acumulado {total:0.0000}";
                if(!decision.aceptada)
                {
                    for(int i=0;i<4;i++){line.enabled=i%2==0;yield return new WaitForSeconds(.25f);}
                    Destroy(line.gameObject);
                }
                else yield return new WaitForSeconds(1);
            }
            patrolActor=Guardian("Auri de patrullaje",data.puntos[0].ToWorld(),Mint,2);
            Ready=true;Status=PatrolSummary();
        }

        string PatrolSummary() => $"{Patrol.arbol.Length} tramos    ·    {Patrol.componentes} componente(s)    ·    Árbol {Patrol.costo_arbol:0.0000}\nTodos los pares {Patrol.costo_candidatas:0.000}    ·    Ahorro {Patrol.costo_candidatas-Patrol.costo_arbol:0.000}\nRutas {Patrol.tiempo_rutas_ms:0.0} ms    ·    Kruskal {Patrol.tiempo_kruskal_ms:0.00} ms";

        public void StartPatrol()
        {
            if(Mode!=GardenMode.Patrol || !Ready || Walking)return;
            StartCoroutine(WalkPatrol());
        }

        IEnumerable<GridCell> Tour(int point,int parent)
        {
            foreach(var edge in Patrol.arbol)
            {
                if(edge.desde!=point && edge.hasta!=point)continue;
                int next=edge.desde==point?edge.hasta:edge.desde;
                if(next==parent)continue;
                var outward=edge.desde==point?edge.ruta:edge.ruta.Reverse();
                foreach(var cell in outward.Skip(1))yield return cell;
                foreach(var cell in Tour(next,point))yield return cell;
                foreach(var cell in outward.Reverse().Skip(1))yield return cell;
            }
        }

        IEnumerator WalkPatrol()
        {
            Walking=true;Status="Auri recorre los tramos desde P1 y regresa por los mismos senderos.";
            var route=new List<GridCell>{Patrol.puntos[0]};route.AddRange(Tour(0,-1));
            float progress=0;
            while(progress<route.Count-1)
            {
                progress=Mathf.Min(route.Count-1,progress+Time.deltaTime*26);
                int i=(int)progress;
                Vector3 from=route[i].ToWorld(),to=route[Math.Min(i+1,route.Count-1)].ToWorld();
                patrolActor.position=Vector3.Lerp(from,to,progress-i);
                if(from!=to)patrolActor.rotation=Quaternion.LookRotation(to-from);
                yield return null;
            }
            Walking=false;Status="Regreso a P1    ·    "+PatrolSummary();
        }
    }
}
