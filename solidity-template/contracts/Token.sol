// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DarkBotToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 1_000_000 * 10**18;
    uint256 public presalePrice = 0.001 ether;
    bool public presaleActive = true;
    mapping(address => bool) public whitelist;
    
    event PresalePurchase(address buyer, uint256 amount, uint256 cost);
    
    constructor() ERC20("DarkBot AI", "DBAI") Ownable(msg.sender) {
        _mint(address(this), MAX_SUPPLY);
    }
    
    function addToWhitelist(address[] calldata users) external onlyOwner {
        for (uint i = 0; i < users.length; i++) whitelist[users[i]] = true;
    }
    
    function buyPresale() external payable {
        require(presaleActive, "Presale not active");
        require(whitelist[msg.sender], "Not whitelisted");
        require(msg.value > 0, "Send ETH to buy");
        uint256 tokens = (msg.value * 10**18) / presalePrice;
        _transfer(address(this), msg.sender, tokens);
        emit PresalePurchase(msg.sender, tokens, msg.value);
    }
    
    function withdrawETH() external onlyOwner {
        (bool ok,) = owner().call{value: address(this).balance}("");
        require(ok, "Withdraw failed");
    }
}
