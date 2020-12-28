.PHONY: all clean


all:
	bash install.sh

pip:
	bash install.sh --pip

clean:
	bash uninstall.sh
