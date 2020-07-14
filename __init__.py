from flask import render_template, request, redirect, url_for, Blueprint, session, send_file, Response
from CTFd.utils.decorators import ratelimit, authed_only, admins_only
from CTFd.utils.logging import log
from CTFd.utils.helpers import get_errors
import os 
import subprocess

def load(app):
    app.db.create_all()
    openvpn = Blueprint('openvpn', __name__, template_folder='templates')

    # Each of the strings in the settings file are added as a line in the .ovpn file
    settings = []
    plugin_root = os.path.dirname(os.path.abspath(__file__))
    settings_file_path = os.path.join(plugin_root, 'settings.txt')
    settings_file = open(settings_file_path)
    for line in settings_file:
        settings.append(line)
    # Done with file
    settings_file.close()

    # Uploads a .ovpn config file to the user. Requires permission to access certificates files and keys in the easyrsa folder
    @openvpn.route('/openvpn_get_file', methods=['GET'])
    @authed_only
    @ratelimit(method="GET", limit=10, interval=60)
    def openvpn_get_file():
        # Default path in debian
        path = '/etc/openvpn/easy-rsa/'

        # Check if the user has generated a certfificate before
        username = session["name"]
        isFile = os.path.isfile(path + 'pki/issued/' + username + '.crt') 
        if not isFile:
            # Build client key and cert if there isn't one on the server
            cmd = ['./easyrsa build-client-full ' + username + ' nopass']
            subprocess.call(cmd, cwd=path, shell=True)

        # Add all the settings strings to one string with newlines
        config_file = ''
        for entry in settings:
            config_file += entry

        # Add certificate
        config_file += '\n<cert>\n'
        f = open(path + 'pki/issued/' + username + '.crt', "r")
        config_file += f.read()
        config_file += '</cert>'

        # Add private key
        config_file += '\n\n<key>\n'
        f = open(path + 'pki/private/' + username + '.key', "r")
        config_file += f.read()
        config_file += '</key>'

        # Send the resulting string as a .ovpn file
        return Response(config_file, mimetype="text/ovpn", headers={"Content-disposition":
                "attachment; filename=" + username + ".ovpn"})

    # Revokes the users access rights, currently deletes the cert and key, then adds them to a list in index.txt as R for Revoked.
    @openvpn.route('/openvpn_revoke', methods=['GET'])
    @authed_only
    @ratelimit(method="GET", limit=10, interval=60)
    def openvpn_revoke():
        path = '/etc/openvpn/easy-rsa/'
        username = session["name"]
        # Revoke user certificate
        cmd = ['./easyrsa --batch revoke ' + username]
        subprocess.call(cmd, cwd=path, shell=True)
        # Update crl
        cmd = ['./easyrsa --batch gen-crl']
        subprocess.call(cmd, cwd=path, shell=True)
        return redirect('/vpn')

    # Landing page for the ctfd page
    @openvpn.route('/vpn', methods=['GET'])
    @authed_only
    def vpn_page():
        return render_template('download_page.html')

    # Landing page for the ctfd page
    @openvpn.route('/admin/vpn/settings', methods=['GET', 'POST'])
    @admins_only
    def vpn_settings():
        if request.method == "GET":
            settings_string = ''
            for entry in settings:
                settings_string += entry
            return render_template('vpn_settings.html', current_settings=settings_string)
        else:
            data = request.get_json()
            new_settings = data['settings']
            # Update file
            try:
                settings_file = open(settings_file_path, 'wt')
                for line in new_settings:
                    settings_file.write(line)
                # Done with file
                settings_file.close()
                return "Update succesful"
            except Exception as e:
                errors = ["Error with file writing: " + e]
                return render_template('vpn_settings.html', current_settings=settings, errors=errors)

    app.register_blueprint(openvpn)
