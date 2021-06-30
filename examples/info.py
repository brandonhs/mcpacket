from mcpacket import protocol

protoc = protocol.Protocol(host='127.0.0.1', port=25565)
protoc.connect()

print(f'{protoc.description.text}')
print(f'Online Players: {protoc.player_count}/{protoc.player_max}')
print('-' * 20)

for player in protoc.player_list:
    print(f'{player.name} - {player.id}')
