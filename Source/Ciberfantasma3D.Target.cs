using UnrealBuildTool;
using System.Collections.Generic;

public class Ciberfantasma3DTarget : TargetRules
{
    public Ciberfantasma3DTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("Ciberfantasma3D");
    }
}
