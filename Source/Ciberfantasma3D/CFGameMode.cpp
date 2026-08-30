#include "CFGameMode.h"
#include "CFHUD.h"
#include "CFGameState.h"
#include "CFPlayerCharacter.h"

ACFGameMode::ACFGameMode()
{
    DefaultPawnClass = ACFPlayerCharacter::StaticClass();
    GameStateClass = ACFGameState::StaticClass();
    HUDClass = ACFHUD::StaticClass();
}
