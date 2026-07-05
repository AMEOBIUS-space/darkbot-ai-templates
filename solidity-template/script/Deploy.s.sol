pragma solidity ^0.8.20;
import "forge-std/Script.sol";
import "../contracts/Token.sol";
contract DeployScript is Script {
    function run() external {
        vm.startBroadcast(vm.envUint("PRIVATE_KEY"));
        DarkBotToken token = new DarkBotToken();
        console.log("Deployed:", address(token));
        vm.stopBroadcast();
    }
}
