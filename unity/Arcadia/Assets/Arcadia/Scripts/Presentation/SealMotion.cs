using UnityEngine;

namespace Arcadia
{
    // Cosmetic animation only: the navigator or player controller owns translation.
    public sealed class SealMotion : MonoBehaviour
    {
        Transform body,left,right,tail;
        Vector3 bodyRest,bodyScale,bodyUp,lastPosition;
        Quaternion bodyRotation,leftRest,rightRest,tailRest;
        Vector3 bodyForward,leftAxis,rightAxis,tailAxis;
        float phase,activity;
        Transform Find(string name)
        {
            foreach(var t in GetComponentsInChildren<Transform>())if(t.name==name)return t;
            return null;
        }
        void Start()
        {
            body=Find("SealBodyPivot");left=Find("LeftFlipperPivot");right=Find("RightFlipperPivot");tail=Find("TailPivot");
            Vector3 forward=transform.parent.forward;
            if(body)
            {
                bodyRest=body.localPosition;bodyScale=body.localScale;bodyRotation=body.localRotation;
                bodyUp=body.parent.InverseTransformDirection(Vector3.up);
                bodyForward=body.InverseTransformDirection(forward);
            }
            if(left){leftRest=left.localRotation;leftAxis=left.InverseTransformDirection(forward);}
            if(right){rightRest=right.localRotation;rightAxis=right.InverseTransformDirection(forward);}
            if(tail){tailRest=tail.localRotation;tailAxis=tail.InverseTransformDirection(transform.parent.right);}
            lastPosition=transform.parent.position;
        }
        void OnEnable(){if(transform.parent)lastPosition=transform.parent.position;activity=0;}
        void LateUpdate()
        {
            Vector3 current=transform.parent.position;
            float distance=Vector3.Distance(current,lastPosition);lastPosition=current;
            // Teleports such as Reset must not look like a burst of locomotion.
            float speed=distance>.8f?0:distance/Mathf.Max(Time.deltaTime,.0001f);
            activity=Mathf.Lerp(activity,Mathf.Clamp01(speed/1.8f),1-Mathf.Exp(-Time.deltaTime*9));
            phase+=Time.deltaTime*(2+speed*3.2f);
            float wave=Mathf.Sin(phase);
            if(body)
            {
                body.localPosition=bodyRest+bodyUp*(Mathf.Max(0,wave)*.018f*activity);
                body.localRotation=bodyRotation*Quaternion.AngleAxis(wave*3.2f*activity,bodyForward);
                body.localScale=bodyScale*(1+Mathf.Sin(Time.time*1.8f)*.004f*(1-activity));
            }
            if(left)left.localRotation=leftRest*Quaternion.AngleAxis((wave*15+6)*activity,leftAxis);
            if(right)right.localRotation=rightRest*Quaternion.AngleAxis((-wave*15-6)*activity,rightAxis);
            if(tail)tail.localRotation=tailRest*Quaternion.AngleAxis(Mathf.Sin(phase+.8f)*12*activity,tailAxis);
        }
    }
}
