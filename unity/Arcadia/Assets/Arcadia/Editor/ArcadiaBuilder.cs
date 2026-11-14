using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Arcadia.Editor
{
    public static class ArcadiaBuilder
    {
        const string ScenePath="Assets/Arcadia/Scenes/ArcadiaGarden.unity";
        [MenuItem("Arcadia/Crear o actualizar escena")]
        public static void BuildScene()
        {
            Directory.CreateDirectory("Assets/Arcadia/Scenes");Directory.CreateDirectory("Assets/Arcadia/Materials");
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var lit=AssetDatabase.LoadAssetAtPath<Material>("Assets/Arcadia/Materials/ArcadiaLit.mat");
            if(lit==null){lit=new Material(Shader.Find("Universal Render Pipeline/Lit"));AssetDatabase.CreateAsset(lit,"Assets/Arcadia/Materials/ArcadiaLit.mat");}
            lit.enableInstancing=true;lit.SetFloat("_Smoothness",.25f);
            // Runtime materials share this keyword; retain the emissive shader variant in players.
            lit.EnableKeyword("_EMISSION");lit.SetColor("_EmissionColor",Color.black);
            var world=new GameObject("Arcadia - jardin procedural del dataset").AddComponent<ArcadiaWorld>();world.LitTemplate=lit;
            world.ArchModel=Model("RuinArch");world.ColumnModel=Model("RuinColumn");world.FernModel=Model("GardenFern");world.RockModel=Model("RuinRockCluster");
            var cameraObject=new GameObject("Main Camera",typeof(Camera),typeof(AudioListener),typeof(UniversalAdditionalCameraData),typeof(ArcadiaCamera));
            cameraObject.tag="MainCamera";var camera=cameraObject.GetComponent<Camera>();camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.20f,.29f,.24f);camera.allowHDR=true;camera.allowMSAA=true;
            var additional=cameraObject.GetComponent<UniversalAdditionalCameraData>();additional.renderPostProcessing=true;additional.antialiasing=AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            var rig=cameraObject.GetComponent<ArcadiaCamera>();rig.Snap();
            var sun=new GameObject("Sol de la tarde").AddComponent<Light>();sun.type=LightType.Directional;sun.color=new Color(1,.94f,.82f);sun.intensity=1.8f;sun.shadows=LightShadows.Soft;sun.shadowStrength=.72f;sun.shadowBias=.04f;sun.shadowNormalBias=.3f;sun.transform.rotation=Quaternion.Euler(48,-42,0);
            RenderSettings.sun=sun;RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.55f,.64f,.68f);RenderSettings.ambientIntensity=1;
            var fill=new GameObject("Luz del cielo").AddComponent<Light>();fill.type=LightType.Directional;fill.color=new Color(.58f,.75f,.83f);fill.intensity=.45f;fill.shadows=LightShadows.None;fill.transform.rotation=Quaternion.Euler(62,140,0);
            RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;RenderSettings.fogColor=new Color(.31f,.40f,.33f);RenderSettings.fogDensity=.011f;
            var volume=new GameObject("Color del jardin").AddComponent<Volume>();volume.isGlobal=true;
            var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Arcadia/Materials/GardenAtmosphere.asset");
            if(profile==null)
            {
                profile=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(profile,"Assets/Arcadia/Materials/GardenAtmosphere.asset");
                var tone=profile.Add<Tonemapping>();tone.mode.Override(TonemappingMode.ACES);
                var bloom=profile.Add<Bloom>();bloom.threshold.Override(1.2f);bloom.intensity.Override(.25f);bloom.scatter.Override(.65f);
                var colors=profile.Add<ColorAdjustments>();colors.postExposure.Override(.3f);colors.contrast.Override(12);colors.saturation.Override(-6);
                var vignette=profile.Add<Vignette>();vignette.intensity.Override(.16f);vignette.smoothness.Override(.5f);
                foreach(var c in profile.components)AssetDatabase.AddObjectToAsset(c,profile);
            }
            volume.sharedProfile=profile;
            var game=new GameObject("Arcadia - experiencia jugable").AddComponent<ArcadiaGame>();game.World=world;game.Rig=rig;game.AuriModel=Model("Auri");
            game.FocaWatonaModel=Model("FocaWatona");
            game.FocaSkin=SealMaterial("FocaSkin",Color.white,.23f,AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Arcadia/Art/FocaWatona_Albedo.png"));
            game.FocaCream=SealMaterial("FocaCream",new Color(.88f,.9f,.87f),.22f);
            game.FocaEyes=SealMaterial("FocaEyes",new Color(.012f,.018f,.02f),.84f);
            game.FocaNose=SealMaterial("FocaNose",new Color(.055f,.065f,.065f),.4f);
            game.FocaWhiskers=SealMaterial("FocaWhiskers",new Color(.64f,.69f,.69f),.24f);
            game.FocaEyelids=SealMaterial("FocaEyelids",new Color(.18f,.23f,.23f),.15f);
            PlayerSettings.companyName="ArcadiaLabs";PlayerSettings.productName="Arcadia - El jardin de los guardianes";
            // This local desktop demonstration connects to the loopback Python HTTP server.
            PlayerSettings.insecureHttpOption=InsecureHttpOption.AlwaysAllowed;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.StandaloneWindows64,false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.StandaloneWindows64,new[]{GraphicsDeviceType.Direct3D11});
            PlayerSettings.defaultScreenWidth=1600;PlayerSettings.defaultScreenHeight=900;PlayerSettings.fullScreenMode=FullScreenMode.Windowed;PlayerSettings.runInBackground=true;
            QualitySettings.vSyncCount=1;
            EditorSceneManager.SaveScene(scene,ScenePath);EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(ScenePath,true)};
            AssetDatabase.SaveAssets();
            Debug.Log("ARCADIA_SCENE_READY "+ScenePath);
        }
        static GameObject Model(string name)=>AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Arcadia/Art/"+name+".fbx");
        static Material SealMaterial(string name,Color color,float smoothness,Texture texture=null)
        {
            string path="Assets/Arcadia/Materials/"+name+".mat";
            var material=AssetDatabase.LoadAssetAtPath<Material>(path);
            if(material==null){material=new Material(Shader.Find("Universal Render Pipeline/Lit"));AssetDatabase.CreateAsset(material,path);}
            material.SetColor("_BaseColor",color);material.SetFloat("_Smoothness",smoothness);material.SetFloat("_Metallic",0);
            material.SetTexture("_BaseMap",texture);material.DisableKeyword("_EMISSION");material.enableInstancing=true;
            EditorUtility.SetDirty(material);return material;
        }

        public static void PrepareAndCheck()
        {
            BuildScene();Navigation.Editor.NavigationChecks.Run();
            if(Model("Auri")==null)throw new Exception("Auri model was not imported.");
            if(Model("FocaWatona")==null)throw new Exception("Foca Watona model was not imported.");
            Debug.Log("ARCADIA_CHECKS_PASSED");
        }
        [MenuItem("Arcadia/Compilar Windows")]
        public static void BuildWindows()
        {
            BuildScene();Directory.CreateDirectory("Builds/Arcadia");
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{ScenePath},locationPathName="Builds/Arcadia/Arcadia.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});
            if(report.summary.result!=UnityEditor.Build.Reporting.BuildResult.Succeeded)throw new Exception("Arcadia Windows build failed: "+report.summary.result);
            Debug.Log("ARCADIA_BUILD_READY "+report.summary.outputPath);
        }
    }
}
