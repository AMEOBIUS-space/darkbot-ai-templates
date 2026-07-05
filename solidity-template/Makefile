.PHONY: install demo test deploy

install:
	forge install

demo:
	python demo.py

test:
	forge test

deploy:
	forge create contracts/Token.sol:DarkBotToken --rpc-url $(RPC_URL) --private-key $(PRIVATE_KEY)
