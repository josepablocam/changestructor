.PHONY: all clean


all:
	bash install.sh

docker:
	docker build --network=host -t chg-container .

clean:
	bash uninstall.sh
