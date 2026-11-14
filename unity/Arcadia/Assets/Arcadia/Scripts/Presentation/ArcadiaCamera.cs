using UnityEngine;
using UnityEngine.EventSystems;

namespace Arcadia
{
    public sealed class ArcadiaCamera : MonoBehaviour
    {
        public Vector3 Focus=new Vector3(107.5f,0,98);
        public Transform Follow;
        public ArcadiaWorld World;
        public bool CloseView;
        public float FollowHeight=.65f;
        public float Distance=48, Yaw=-10, Pitch=62;
        Camera cameraComponent;
        Vector3 velocity;
        void Awake(){cameraComponent=GetComponent<Camera>();cameraComponent.fieldOfView=43;cameraComponent.nearClipPlane=.1f;cameraComponent.farClipPlane=400;Snap();}
        public void ResetView(){Follow=null;CloseView=false;Focus=new Vector3(107.5f,0,98);Distance=48;Yaw=-10;Pitch=62;Snap();}
        public void Snap(){Vector3 offset=Quaternion.Euler(0,Yaw,0)*new Vector3(0,Mathf.Sin(Pitch*Mathf.Deg2Rad),Mathf.Cos(Pitch*Mathf.Deg2Rad))*Distance;transform.position=Focus+offset;transform.LookAt(Focus);}
        void LateUpdate()
        {
            bool overUI=EventSystem.current!=null&&EventSystem.current.IsPointerOverGameObject();
            if(Input.GetMouseButton(1)){Yaw+=Input.GetAxis("Mouse X")*3.5f;Pitch=Mathf.Clamp(Pitch-Input.GetAxis("Mouse Y")*2,25,80);}
            if(!overUI)Distance=Mathf.Clamp(Distance-Input.mouseScrollDelta.y*(CloseView?.8f:2),CloseView?3:10,CloseView?20:100);
            if(Follow!=null)Focus=Follow.position+Vector3.up*FollowHeight;
            else
            {
                Vector3 right=transform.right;right.y=0;right.Normalize();Vector3 forward=Vector3.Cross(right,Vector3.up);
                Focus+=(right*Input.GetAxisRaw("Horizontal")+forward*Input.GetAxisRaw("Vertical"))*Time.deltaTime*Distance*.45f;
            }
            Vector3 offset=Quaternion.Euler(0,Yaw,0)*new Vector3(0,Mathf.Sin(Pitch*Mathf.Deg2Rad),Mathf.Cos(Pitch*Mathf.Deg2Rad))*Distance;
            Vector3 desired=Focus+offset;
            if(Follow!=null&&World!=null)desired=World.ClearCameraSight(Focus,desired);
            Vector3 next=Vector3.SmoothDamp(transform.position,desired,ref velocity,.18f);
            if(Follow!=null&&World!=null)next=World.ClearCameraSight(Focus,next);
            transform.position=next;transform.LookAt(Focus);
            if(World!=null)World.UpdateCameraOcclusion(transform.position,Focus,Follow!=null);
        }
    }

    public sealed class AuriMotion : MonoBehaviour
    {
        Transform body,head,leftArm,rightArm,leftLeg,rightLeg;
        Quaternion armL,armR,legL,legR,headRest;
        Vector3 bodyRest,lastPosition;
        Vector3 bodyUp,headUp;
        float phase,activity;
        Transform Find(string n){foreach(var t in GetComponentsInChildren<Transform>())if(t.name==n)return t;return null;}
        void Start()
        {
            body=Find("BodyPivot");head=Find("HeadPivot");leftArm=Find("LeftArmPivot");rightArm=Find("RightArmPivot");leftLeg=Find("LeftLegPivot");rightLeg=Find("RightLegPivot");
            if(body){bodyRest=body.localPosition;bodyUp=body.parent.InverseTransformDirection(Vector3.up);}
            if(head){headRest=head.localRotation;headUp=head.InverseTransformDirection(Vector3.up);}
            if(leftArm)armL=leftArm.localRotation;if(rightArm)armR=rightArm.localRotation;
            if(leftLeg)legL=leftLeg.localRotation;if(rightLeg)legR=rightLeg.localRotation;
            lastPosition=transform.position;
        }
        void LateUpdate()
        {
            float speed=(transform.position-lastPosition).magnitude/Mathf.Max(Time.deltaTime,.0001f);lastPosition=transform.position;
            activity=Mathf.Lerp(activity,Mathf.Clamp01(speed/1.8f),1-Mathf.Exp(-Time.deltaTime*10));phase+=Time.deltaTime*(speed*4+1);
            float swing=Mathf.Sin(phase)*24*activity;
            if(leftLeg)leftLeg.localRotation=legL*Quaternion.Euler(swing,0,0);
            if(rightLeg)rightLeg.localRotation=legR*Quaternion.Euler(-swing,0,0);
            if(leftArm)leftArm.localRotation=armL*Quaternion.Euler(-swing*.7f,0,0);
            if(rightArm)rightArm.localRotation=armR*Quaternion.Euler(swing*.7f,0,0);
            if(body)body.localPosition=bodyRest+bodyUp*(Mathf.Sin(phase*2)*.012f*activity+Mathf.Sin(Time.time*1.7f)*.003f);
            if(head)head.localRotation=headRest*Quaternion.AngleAxis(Mathf.Sin(Time.time*.7f)*5*(1-activity),headUp);
        }
    }
}
