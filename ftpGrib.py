from bs4 import BeautifulSoup as bs
import os
from urllib.request import urlopen
import ssl


def confereDataDinamico(url: str, dataComeco: str, dataFinal: str, ano: str):

    if ano in url:
        listaComeco = dataComeco.split("/")
        listaFinal = dataFinal.split("/")

        dados = url.split("/")
        indexAno = dados.index(ano)
        try:
            mes = int(dados[indexAno+1])
        except:##nao entrou em algum mes ainda
            return 1
        if mes == int(listaComeco[1]): #mes comeco
            try:
                dia = int(dados[indexAno+2])
            except:
                return 1

            if dia >= int(listaComeco[0]):
                return 1

        elif mes == int(listaFinal[1]): #mes final

            try:
                dia = int(dados[indexAno+2])
            except:
                return 1

            if dia <= int(listaFinal[0]):
                return 1


        elif mes > int(listaComeco[1]) and mes < int(listaFinal[1]):
            return 1

    elif ano not in url:
        return 1

    return 0


def parseftpdir2(data):
    """
    :param data: Bytes do html doc
    :return: Lista com os diretorios filhos acessiveis no html
    """
    htmlString = str(data)
    inDir = list()
    soup = bs(htmlString, "html.parser")
    As = soup.find_all(href=True)
    for i in As:
        if "?C" not in str(i) and i.contents[0] != "Parent Directory":
            inDir.append(i.contents[0])
    return inDir


def arrumarNewDir(root: str, next: str):
    new = str()
    for char in next:
        if char == "/":
            new = new+"\\"
        else:
            new = new+char
    if root[-1] != "\\":
        root = root+"\\"
    root = root+new
    return root


def ftpRequest(url, pemFile=""):
    """
    Realiza a requisicao FTP utilizando.
    :param url: link do servidor ftp
    :param pemFile: (opcional) path do arquivo certificado .pem
    :return:
    """
    if pemFile != "":
        with urlopen(url) as response:
            data = response.read()
    else:
        context = ssl.create_default_context(cafile=pemFile)
        with urlopen(url, context=context) as response:
            data = response.read()

    return data


def downloadTudoDinamico(urlRoot, dirRoot, dataComeco, dataFinal, ano):
    """
    Dado um servidor ftp, salva todos os arquivos de todos os diretorios que contenham .grib e um .ctl por dia
    :param urlRoot: Url do servidor ftp
    :param dirRoot: Diretorio para salvar os arquivos
    :param dataComeco: DD/MM de comeco
    :param dataFinal: DD/MM final
    """

    permFile = "ftp-cptec-inpe-br-chain.pem"
    validacao = confereDataDinamico(urlRoot, dataComeco, dataFinal, ano)
    ctlUnico = True

    if validacao == 0:
        print("Passou -- " + urlRoot)
        return

    print("Download url: " + str(urlRoot))
    data = ftpRequest(urlRoot, permFile)

    inDirList = parseftpdir2(data)

    for item in inDirList:
        if "/" in str(item): #achou uma pasta
            newDir = arrumarNewDir(dirRoot, str(item))
            try:
                os.mkdir(newDir)
            except:
                pass
            downloadTudoDinamico(urlRoot+str(item), newDir, dataComeco, dataFinal)
        elif (".grib" in str(item)): #achou arquivo com .grib
            if not (os.path.exists(dirRoot+str(item))):
                data = ftpRequest(urlRoot+str(item), permFile)
                file = dirRoot+str(item)
                with open(file, "wb") as bFile:
                    bFile.write(data)
                    bFile.close()
        elif(".ctl" in str(item) and ctlUnico and ".grh" not in str(item)): #achou arquivo .ctl e é o primeiro.
            ctlUnico = False
            if(os.path.exists((dirRoot+str(item)))): #Arquivo ctl já existe. É necessário apenas um por dia.
                return
            data = ftpRequest(urlRoot+str(item), permFile)
            file = dirRoot+str(item)
            with open(file, "wb") as bFile:
                bFile.write(data)
                bFile.close()


def controleDinamico(newdir: str, ano: str, dataComeco: str, dataFinal: str, url: str, ):
    """
    Função principal. Realiza o download de todos os arquivos .grib, e um .clt por dia. !Não itera por diferentes anos!
    Caso ocorra
    :param newdir: Diretorio já criado em que os dados e novas pastas serão criados
    :param ano: Ano, em string, que será considerado.
    :param dataComeco: String no formato "DD/MM". Começo do período desejado.
    :param dataFinal: String no formato "DD/MM". Final do perídod desejado.
    :param url: Link do diretorio do servidor FTP do INPE onde os arquivos serão procurados.
    """
    try:
        downloadTudoDinamico(url, newdir, dataComeco, dataFinal, ano)
    except OSError as e:
        print("-----------------ERROR OS: ")
        print(e)
        return
    except Exception as e:
        print(e)
        controleDinamico(newdir, dataComeco, dataFinal, url)


def apagarPastasVaziasRecursivo(dir: str):
    """
    Dado um diretorio, apaga todas as pastas dentro dele que estejam vazias.
    :param dir: Diretorio nó
    """
    conteudo = os.listdir(dir)
    for item in conteudo:
        if os.path.isdir(item):
            apagarPastasVaziasRecursivo(os.path.join(dir, item))
    conteudo = os.listdir(dir)
    if len(conteudo) == 0:
        os.rmdir(dir)


def main():
    # Exemplo de utilização do código.
    controleDinamico("F:\\Dados INPE - BAM, BRAMS, MERGE\\brams",
                 "2024", "01/05", "23/05", "https://ftp.cptec.inpe.br/modelos/tempo/BRAMS/")

    # Não necessário, apenas para manter apenas pastas que possuem arquivos.
    apagarPastasVaziasRecursivo("F:\\Dados INPE - BAM, BRAMS, MERGE")


if __name__ == '__main__':
    main()