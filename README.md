Installation guide:
This plugin uses openVPN for users to connect to the server.
To install this plugin you need to set up an openVPN server on the host machine. These are the steps used to enable the vpn, tested and working on debian:
1. Follow this guide on the debian wiki for testing, configuering and launching your openvpn server: https://wiki.debian.org/OpenVPN

1 b. I recomend using systemd service to launch the server after you have tested it and it works. To launch it you simply need to run <code>openvpn /etc/openvpn/server/server.conf</code> 

2. Change the settings object in __init__.py to reflect the client settings that match your server.conf file for the openvpn server

3. Add a page through the admin panel that directs the user to the /vpn endpoint, thats where the client download page is
