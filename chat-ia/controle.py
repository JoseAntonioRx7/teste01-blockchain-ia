# Demonstaçrãp de um dict usando elementos k e v para poder representar eles
# Uso do for e o começo de um chatbot onde seu nome é TedGo

chatbot = {"Nome": "TedGo", "Aplicacoes": "Hospitais", "Tecnologia": "Blockchain"}
print(chatbot)
print(type(chatbot))
print('-'*30)

for k,v in chatbot.items():
    print(f'keys: {k} , values: {v}')
print('Dicionario OK!')

print('-'*30)
print('Chat aberto para consulta.')
print('\nOla! Sou o novo chatbot da TedGo.')

nome = input('Qual o seu nome: ')
print(f"Prazer em te conhecer {nome}")



