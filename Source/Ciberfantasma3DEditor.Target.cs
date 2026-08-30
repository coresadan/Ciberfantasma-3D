using UnrealBuildTool;
using System.Collections.Generic;

public class Ciberfantasma3DEditorTarget : TargetRules
{
    public Ciberfantasma3DEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("Ciberfantasma3D");
    }
}
