using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Arcadia.Navigation;

namespace Arcadia
{
    public sealed partial class ArcadiaHud
    {
        readonly List<GameObject> navigationPanels=new List<GameObject>();
        readonly List<Text> modeTabs=new List<Text>();
        RectTransform graphPanel, tablePanel, capacityPanel;
        Text graphTitle, technique, graphStatus, primary, secondary, capacityLabel;
        Slider capacitySlider;
        SeleccionBotin drawnLoot;
        Image[][] squares;
        Text[] itemLabels;
        int rowsDrawn, stepsDrawn;
        GardenMode displayed;
        GardenModes Modes => game.Modes;

        void InitializeModes(RectTransform header)
        {
            foreach(Transform child in canvas)if(child!=header)navigationPanels.Add(child.gameObject);
            var tabs=Panel("Modos del jardín",canvas,430,27,470,52,ink);
            string[] names={"Navegación","Pasillo","Patrullaje","Botín"};
            for(int i=0;i<names.Length;i++)
            {
                var selected=(GardenMode)i;
                modeTabs.Add(Button(tabs,names[i],8+i*115,8,110,36,()=>{Modes.Select(selected);Refresh();}));
            }
            graphPanel=Panel("Observatorio del algoritmo",canvas,32,144,378,263,ink);
            graphTitle=Label(graphPanel,"",18,16,342,38,24,cream,FontStyle.Bold);
            technique=Label(graphPanel,"",18,60,342,48,15,mint);
            graphStatus=Label(graphPanel,"",18,116,342,86,15,cream);
            primary=Button(graphPanel,"",18,211,170,36,PrimaryAction,true);
            secondary=Button(graphPanel,"Otros puntos",197,211,160,36,()=>Modes.OtherPoints());
            capacityPanel=Panel("Capacidad de la mochila",canvas,32,419,378,64,ink);
            capacityLabel=Label(capacityPanel,"",12,8,145,42,14,cream);
            var track=Panel("Deslizador",capacityPanel,145,9,215,42,ink);
            var rail=Panel("Escala",track,4,19,207,5,muted);
            var handle=Panel("Peso",rail,0,-8,18,20,mint);
            capacitySlider=track.gameObject.AddComponent<Slider>();
            capacitySlider.targetGraphic=handle.GetComponent<Image>();capacitySlider.handleRect=handle;
            capacitySlider.minValue=1;capacitySlider.maxValue=60;capacitySlider.wholeNumbers=true;
            capacitySlider.SetValueWithoutNotify(Modes.Capacity);
            capacitySlider.onValueChanged.AddListener(v=>Modes.SetCapacity((int)v));
            graphPanel.gameObject.SetActive(false);capacityPanel.gameObject.SetActive(false);
        }

        void PrimaryAction()
        {
            if(Modes.Failed){Modes.Reload();return;}
            switch(Modes.Mode)
            {
                case GardenMode.Corridor: Modes.ToggleCut();break;
                case GardenMode.Patrol: Modes.StartPatrol();break;
                case GardenMode.Loot: Modes.OpenChest();break;
            }
        }

        bool RefreshModes()
        {
            if(!graphPanel)return false;
            var mode=Modes.Mode;
            bool navigation=mode==GardenMode.Navigation;
            if(mode!=displayed)
            {
                foreach(var panel in navigationPanels)panel.SetActive(navigation);
                displayed=mode;
            }
            for(int i=0;i<modeTabs.Count;i++)
                modeTabs[i].transform.parent.GetComponent<Image>().color=i==(int)mode?new Color(.26f,.47f,.35f):new Color(.12f,.19f,.15f);
            graphPanel.gameObject.SetActive(!navigation);
            capacityPanel.gameObject.SetActive(mode==GardenMode.Loot);
            if(drawnLoot!=Modes.Loot)
            {
                if(tablePanel){tablePanel.gameObject.SetActive(false);Destroy(tablePanel.gameObject);}
                drawnLoot=Modes.Loot;rowsDrawn=stepsDrawn=0;
                if(drawnLoot!=null)BuildTable();
            }
            if(navigation)return false;
            graphTitle.text=Modes.Info?.nombre ?? "Consultando el motor…";
            technique.text=Modes.Info==null?"":Modes.Info.tecnica+"\n"+Modes.Info.complejidad;
            graphStatus.text=Modes.Status;
            primary.text=Modes.Failed?"Reintentar":mode==GardenMode.Corridor?(Modes.Closed?"Abrir el corte":"Cerrar el corte"):
                mode==GardenMode.Patrol?(Modes.Walking?"Patrullando…":"Patrullar"):(drawnLoot==null?"Abrir cofre":"Repetir selección");
            primary.transform.parent.GetComponent<Button>().interactable=Modes.Failed || Modes.Ready && !Modes.Walking;
            secondary.transform.parent.gameObject.SetActive(mode==GardenMode.Patrol);
            capacityLabel.text=$"Capacidad\n{Modes.Capacity} kg";
            if(drawnLoot!=null)RefreshTable();
            return true;
        }

        void BuildTable()
        {
            int columns=drawnLoot.capacidad+1;
            const float width=690,rowHeight=17;
            float cellWidth=width/columns;
            float height=74+rowHeight*drawnLoot.tabla.Length;
            tablePanel=Panel("Tabla de mochila",canvas,-(width+180),-height-20,width+154,height,ink,true,true);
            Label(tablePanel,"Mejor valor por capacidad (kg)",14,8,400,24,16,cream,FontStyle.Bold);
            Label(tablePanel,"Verde · PD     Rojo · solo voraz     Dorado · reconstrucción",width-260,10,407,20,12,cream);
            for(int c=0;c<columns;c++)
                if(columns<=31 || c%5==0)Label(tablePanel,c.ToString(),146+c*cellWidth,37,cellWidth+4,18,10,muted);
            squares=new Image[drawnLoot.tabla.Length][];
            itemLabels=new Text[drawnLoot.objetos.Length];
            for(int r=0;r<squares.Length;r++)
            {
                float y=55+r*rowHeight;
                var rowLabel=Label(tablePanel,r==0?"Sin objetos":drawnLoot.objetos[r-1].nombre,14,y,128,rowHeight,11,cream);
                if(r>0)itemLabels[r-1]=rowLabel;
                squares[r]=new Image[columns];
                for(int c=0;c<columns;c++)
                {
                    var cell=Panel("Celda",tablePanel,145+c*cellWidth,y,cellWidth-1,rowHeight-1,ink);
                    squares[r][c]=cell.GetComponent<Image>();squares[r][c].sprite=null;
                    if(columns<=31)
                    {
                        var value=Label(cell,drawnLoot.tabla[r][c].ToString(),0,0,cellWidth-1,rowHeight-1,10,Color.white);
                        value.alignment=TextAnchor.MiddleCenter;
                    }
                    cell.gameObject.SetActive(false);
                }
            }
        }

        void RefreshTable()
        {
            if(Modes.Ready)
            {
                foreach(int i in drawnLoot.voraz.elegidos)itemLabels[i].color=new Color(1,.56f,.50f);
                foreach(int i in drawnLoot.optima.elegidos)itemLabels[i].color=mint;
            }
            while(rowsDrawn<Modes.VisibleRows)
            {
                int r=rowsDrawn++;
                for(int c=0;c<squares[r].Length;c++)
                {
                    var cell=squares[r][c];
                    cell.color=Color.Lerp(new Color(.07f,.12f,.11f),new Color(.13f,.47f,.35f),
                        drawnLoot.tabla[r][c]/(float)Math.Max(1,drawnLoot.optima.valor));
                    cell.gameObject.SetActive(true);
                }
            }
            while(stepsDrawn<Modes.Reconstructed)
            {
                var step=drawnLoot.reconstruccion[stepsDrawn++];
                squares[step.Row][step.Column].color=new Color(.55f,.34f,.10f);
            }
        }
    }
}
