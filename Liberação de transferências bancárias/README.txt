------------ README

1) Caso hajam TEDs de mesmo usuário, número do cartão e favorecido, copie uma das duas e cole em uma outra linha da planilha.
Importante reforçar que você cole essa segunda TED *FORA* do range de captura (por padrão: 3)

2) Antes de rodar o script, já deixe setado na planilha principal quais TEDs devem ser rejeitadas. O script captura apenas as 
TEDs cujo o status esteja como "PROCESSANDO"...se você colocar a condição "REJEITADO" o script irá pular o mesmo.

A rejeição das TEDs deverá ser feita manualmente.

3) Lembre de gerar suas credenciais em um arquivo .env , pois na hora de você puxar o arquivo do repositório o arquivo com as
credenciais não será puxado (.gitignore).
