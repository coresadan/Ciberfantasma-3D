using UnrealBuildTool;

public class Ciberfantasma3D : ModuleRules
{
    public Ciberfantasma3D(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "AnimGraphRuntime",
            "Niagara"
        });
    }
}
