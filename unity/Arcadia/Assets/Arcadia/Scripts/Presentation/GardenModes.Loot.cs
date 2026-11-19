using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Arcadia
{
    public sealed partial class GardenModes
    {
        Vector3 ChestSpot => game.StartCell.ToWorld();
        void PrepareChest()
        {
            Vector3 center=ChestSpot;
            Frame(center+Vector3.right,17,52);
            Guardian("Auri y la mochila",center,Mint,1);
            Vector3 chest=center+Vector3.right*1.6f;
            Shape("Cofre",PrimitiveType.Cube,chest+Vector3.up*.38f,new Vector3(1.3f,.76f,.8f),new Color(.42f,.22f,.08f));
            var lid=Shape("Tapa",PrimitiveType.Cube,chest+Vector3.up*(chestOpen?1.03f:.82f),new Vector3(1.35f,.19f,.83f),Amber);
            if(chestOpen)lid.transform.rotation=Quaternion.Euler(-45,0,0);
        }
        IEnumerator ShowLoot()
        {
            var items=Loot.objetos;
            var props=new Transform[items.Length];
            var best=new HashSet<int>(Loot.optima.elegidos);
            var greedy=new HashSet<int>(Loot.voraz.elegidos);
            for(int i=0;i<items.Length;i++)
            {
                float angle=i*2*Mathf.PI/items.Length;
                Vector3 point=ChestSpot+new Vector3(Mathf.Cos(angle)*4,.4f,Mathf.Sin(angle)*3.5f);
                props[i]=Shape(items[i].nombre,i%2==0?PrimitiveType.Cube:PrimitiveType.Sphere,point,Vector3.one*.48f,Amber).transform;
                props[i].rotation=Quaternion.Euler(15,i*31,30);
                Caption(props[i],$"{items[i].nombre}\n{items[i].peso} kg · {items[i].valor} oro",.047f,.75f);
            }
            for(int i=0;i<Loot.tabla.Length;i++)
            {VisibleRows=i+1;Status=$"Tabla de valor óptimo    ·    Fila {i} de {items.Length}";yield return new WaitForSeconds(.14f);}
            for(int i=0;i<Loot.reconstruccion.Length;i++)
            {Reconstructed=i+1;Status="Reconstruyendo la selección óptima";yield return new WaitForSeconds(.09f);}
            var starts=new Vector3[props.Length];
            for(int i=0;i<props.Length;i++)
            {
                starts[i]=props[i].position;
                props[i].GetComponent<Renderer>().sharedMaterial=Paint(best.Contains(i)?Mint:greedy.Contains(i)?Red:Amber);
            }
            for(float t=0;t<1;t+=Time.deltaTime)
            {
                foreach(int index in best)
                    props[index].position=Vector3.Lerp(starts[index],ChestSpot+Vector3.up*.65f,t)+Vector3.up*Mathf.Sin(t*Mathf.PI);
                yield return null;
            }
            foreach(int index in best)props[index].gameObject.SetActive(false);
            Ready=true;Status=$"PD {Loot.optima.valor} oro · {Loot.optima.peso} kg    /    Voraz {Loot.voraz.valor} oro · {Loot.voraz.peso} kg\nVentaja de la PD {Loot.optima.valor-Loot.voraz.valor} oro    ·    {Loot.tiempo_ms:0.000} ms";
        }
    }
}
