"""Gera base/trechos.jsonl e base/FONTES.md a partir da lista abaixo.
Os textos foram copiados do texto oficial da Lei 13.146/2015 (normas.leg.br /
planalto.gov.br). Trechos de outras leis vêm da redação dada por ela.
Uso: python base/construir_base.py
"""
import json, collections
from pathlib import Path

URL_LBI = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
URL_COPIA = "https://normas.leg.br/api/public/binario/33bc4c3d-ac6a-4c9a-b4a3-d83f03d760cb/texto"
LBI, L11126, L10048, L10098, L10257, L12587 = (
    "Lei 13.146/2015", "Lei 11.126/2005", "Lei 10.048/2000",
    "Lei 10.098/2000", "Lei 10.257/2001", "Lei 12.587/2012")
VIA = "redação dada pela Lei 13.146/2015, art. "

# (id, norma, referência, tema, observação, texto)
T = [
("T01", LBI, "art. 2º, caput", "definição", "",
 "Considera-se pessoa com deficiência aquela que tem impedimento de longo prazo de natureza física, mental, intelectual ou sensorial, o qual, em interação com uma ou mais barreiras, pode obstruir sua participação plena e efetiva na sociedade em igualdade de condições com as demais pessoas."),
("T02", LBI, "art. 3º, I", "definição", "",
 "Para fins de aplicação desta Lei, consideram-se: acessibilidade: possibilidade e condição de alcance para utilização, com segurança e autonomia, de espaços, mobiliários, equipamentos urbanos, edificações, transportes, informação e comunicação, inclusive seus sistemas e tecnologias, bem como de outros serviços e instalações abertos ao público, de uso público ou privados de uso coletivo, tanto na zona urbana como na rural, por pessoa com deficiência ou com mobilidade reduzida;"),
("T03", LBI, "art. 3º, III", "definição", "",
 "Para fins de aplicação desta Lei, consideram-se: tecnologia assistiva ou ajuda técnica: produtos, equipamentos, dispositivos, recursos, metodologias, estratégias, práticas e serviços que objetivem promover a funcionalidade, relacionada à atividade e à participação da pessoa com deficiência ou com mobilidade reduzida, visando à sua autonomia, independência, qualidade de vida e inclusão social;"),
("T04", LBI, "art. 3º, IV, a e c", "definição", "trecho resumido com [...]",
 "Para fins de aplicação desta Lei, consideram-se: barreiras: qualquer entrave, obstáculo, atitude ou comportamento que limite ou impeça a participação social da pessoa, bem como o gozo, a fruição e o exercício de seus direitos à acessibilidade, à liberdade de movimento e de expressão, à comunicação, ao acesso à informação, à compreensão, à circulação com segurança, entre outros, classificadas em: a) barreiras urbanísticas: as existentes nas vias e nos espaços públicos e privados abertos ao público ou de uso coletivo; [...] c) barreiras nos transportes: as existentes nos sistemas e meios de transportes;"),
("T05", LBI, "art. 4º, caput e § 1º", "discriminação", "",
 "Toda pessoa com deficiência tem direito à igualdade de oportunidades com as demais pessoas e não sofrerá nenhuma espécie de discriminação. Considera-se discriminação em razão da deficiência toda forma de distinção, restrição ou exclusão, por ação ou omissão, que tenha o propósito ou o efeito de prejudicar, impedir ou anular o reconhecimento ou o exercício dos direitos e das liberdades fundamentais de pessoa com deficiência, incluindo a recusa de adaptações razoáveis e de fornecimento de tecnologias assistivas."),
("T06", LBI, "art. 7º, caput", "denúncia", "",
 "É dever de todos comunicar à autoridade competente qualquer forma de ameaça ou de violação aos direitos da pessoa com deficiência."),
("T07", LBI, "art. 9º, caput, I e IV", "atendimento prioritário", "trecho resumido com [...]",
 "A pessoa com deficiência tem direito a receber atendimento prioritário, sobretudo com a finalidade de: I – proteção e socorro em quaisquer circunstâncias; [...] IV – disponibilização de pontos de parada, estações e terminais acessíveis de transporte coletivo de passageiros e garantia de segurança no embarque e no desembarque;"),
("T08", LBI, "art. 9º, § 1º", "atendimento prioritário", "",
 "Os direitos previstos neste artigo são extensivos ao acompanhante da pessoa com deficiência ou ao seu atendente pessoal, exceto quanto ao disposto nos incisos VI e VII deste artigo."),
("T09", LBI, "art. 40", "benefício", "",
 "É assegurado à pessoa com deficiência que não possua meios para prover sua subsistência nem de tê-la provida por sua família o benefício mensal de 1 (um) salário-mínimo, nos termos da Lei nº 8.742, de 7 de dezembro de 1993."),
("T10", LBI, "art. 44, § 7º", "ingresso", "",
 "O valor do ingresso da pessoa com deficiência não poderá ser superior ao valor cobrado das demais pessoas."),
("T11", LBI, "art. 46, caput", "transporte", "",
 "O direito ao transporte e à mobilidade da pessoa com deficiência ou com mobilidade reduzida será assegurado em igualdade de oportunidades com as demais pessoas, por meio de identificação e de eliminação de todos os obstáculos e barreiras ao seu acesso."),
("T12", LBI, "art. 46, § 1º", "transporte", "",
 "Para fins de acessibilidade aos serviços de transporte coletivo terrestre, aquaviário e aéreo, em todas as jurisdições, consideram-se como integrantes desses serviços os veículos, os terminais, as estações, os pontos de parada, o sistema viário e a prestação do serviço."),
("T13", LBI, "art. 47, caput e § 1º", "estacionamento", "",
 "Em todas as áreas de estacionamento aberto ao público, de uso público ou privado de uso coletivo e em vias públicas, devem ser reservadas vagas próximas aos acessos de circulação de pedestres, devidamente sinalizadas, para veículos que transportem pessoa com deficiência com comprometimento de mobilidade, desde que devidamente identificados. As vagas a que se refere o caput deste artigo devem equivaler a 2% (dois por cento) do total, garantida, no mínimo, 1 (uma) vaga devidamente sinalizada e com as especificações de desenho e traçado de acordo com as normas técnicas vigentes de acessibilidade."),
("T14", LBI, "art. 48, caput, § 1º e § 2º", "transporte", "",
 "Os veículos de transporte coletivo terrestre, aquaviário e aéreo, as instalações, as estações, os portos e os terminais em operação no País devem ser acessíveis, de forma a garantir o seu uso por todas as pessoas. Os veículos e as estruturas de que trata o caput deste artigo devem dispor de sistema de comunicação acessível que disponibilize informações sobre todos os pontos do itinerário. São asseguradas à pessoa com deficiência prioridade e segurança nos procedimentos de embarque e de desembarque nos veículos de transporte coletivo, de acordo com as normas técnicas."),
("T15", LBI, "art. 51, caput e § 1º", "táxi", "",
 "As frotas de empresas de táxi devem reservar 10% (dez por cento) de seus veículos acessíveis à pessoa com deficiência. É proibida a cobrança diferenciada de tarifas ou de valores adicionais pelo serviço de táxi prestado à pessoa com deficiência."),
("T16", LBI, "art. 52, caput", "locadoras", "",
 "As locadoras de veículos são obrigadas a oferecer 1 (um) veículo adaptado para uso de pessoa com deficiência, a cada conjunto de 20 (vinte) veículos de sua frota."),
("T17", LBI, "art. 53", "acessibilidade", "",
 "A acessibilidade é direito que garante à pessoa com deficiência ou com mobilidade reduzida viver de forma independente e exercer seus direitos de cidadania e de participação social."),
("T18", LBI, "art. 55, caput, § 1º e § 2º", "desenho universal", "",
 "A concepção e a implantação de projetos que tratem do meio físico, de transporte, de informação e comunicação, inclusive de sistemas e tecnologias da informação e comunicação, e de outros serviços, equipamentos e instalações abertos ao público, de uso público ou privado de uso coletivo, tanto na zona urbana como na rural, devem atender aos princípios do desenho universal, tendo como referência as normas de acessibilidade. O desenho universal será sempre tomado como regra de caráter geral. Nas hipóteses em que comprovadamente o desenho universal não possa ser empreendido, deve ser adotada adaptação razoável."),
("T19", LBI, "art. 59", "obras na via", "",
 "Em qualquer intervenção nas vias e nos espaços públicos, o poder público e as empresas concessionárias responsáveis pela execução das obras e dos serviços devem garantir, de forma segura, a fluidez do trânsito e a livre circulação e acessibilidade das pessoas, durante e após sua execução."),
("T20", LBI, "art. 63, caput", "internet", "",
 "É obrigatória a acessibilidade nos sítios da internet mantidos por empresas com sede ou representação comercial no País ou por órgãos de governo, para uso da pessoa com deficiência, garantindo-lhe acesso às informações disponíveis, conforme as melhores práticas e diretrizes de acessibilidade adotadas internacionalmente."),
("T21", LBI, "art. 74", "tecnologia assistiva", "",
 "É garantido à pessoa com deficiência acesso a produtos, recursos, estratégias, práticas, processos, métodos e serviços de tecnologia assistiva que maximizem sua autonomia, mobilidade pessoal e qualidade de vida."),
("T22", LBI, "art. 88, caput", "crime", "",
 "Praticar, induzir ou incitar discriminação de pessoa em razão de sua deficiência: Pena – reclusão, de 1 (um) a 3 (três) anos, e multa."),
("T23", LBI, "art. 92, caput", "dados", "",
 "É criado o Cadastro Nacional de Inclusão da Pessoa com Deficiência (Cadastro-Inclusão), registro público eletrônico com a finalidade de coletar, processar, sistematizar e disseminar informações georreferenciadas que permitam a identificação e a caracterização socioeconômica da pessoa com deficiência, bem como das barreiras que impedem a realização de seus direitos."),
("T24", LBI, "art. 95, caput", "atendimento", "trecho resumido com [...]",
 "É vedado exigir o comparecimento de pessoa com deficiência perante os órgãos públicos quando seu deslocamento, em razão de sua limitação funcional e de condições de acessibilidade, imponha-lhe ônus desproporcional e indevido, hipótese na qual serão observados os seguintes procedimentos: [...]"),
("T25", L11126, "art. 1º, caput e § 2º", "cão-guia", VIA + "117",
 "É assegurado à pessoa com deficiência visual acompanhada de cão-guia o direito de ingressar e de permanecer com o animal em todos os meios de transporte e em estabelecimentos abertos ao público, de uso público e privados de uso coletivo, desde que observadas as condições impostas por esta Lei. O disposto no caput deste artigo aplica-se a todas as modalidades e jurisdições do serviço de transporte coletivo de passageiros, inclusive em esfera internacional com origem no território brasileiro."),
("T26", L10048, "art. 1º", "atendimento prioritário", VIA + "111",
 "As pessoas com deficiência, os idosos com idade igual ou superior a 60 (sessenta) anos, as gestantes, as lactantes, as pessoas com crianças de colo e os obesos terão atendimento prioritário, nos termos desta Lei."),
("T27", L10098, "art. 3º, caput e parágrafo único", "calçadas", VIA + "112",
 "O planejamento e a urbanização das vias públicas, dos parques e dos demais espaços de uso público deverão ser concebidos e executados de forma a torná-los acessíveis para todas as pessoas, inclusive para aquelas com deficiência ou com mobilidade reduzida. O passeio público, elemento obrigatório de urbanização e parte da via pública, normalmente segregado e em nível diferente, destina-se somente à circulação de pedestres e, quando possível, à implantação de mobiliário urbano e de vegetação."),
("T28", L10098, "art. 9º, parágrafo único", "semáforo", VIA + "112",
 "Os semáforos para pedestres instalados em vias públicas de grande circulação, ou que deem acesso aos serviços de reabilitação, devem obrigatoriamente estar equipados com mecanismo que emita sinal sonoro suave para orientação do pedestre."),
("T29", L10098, "art. 10-A", "obstáculos", VIA + "112",
 "A instalação de qualquer mobiliário urbano em área de circulação comum para pedestre que ofereça risco de acidente à pessoa com deficiência deverá ser indicada mediante sinalização tátil de alerta no piso, de acordo com as normas técnicas pertinentes."),
("T30", L10098, "art. 2º, VII", "obstáculos", VIA + "112",
 "mobiliário urbano: conjunto de objetos existentes nas vias e nos espaços públicos, superpostos ou adicionados aos elementos de urbanização ou de edificação, de forma que sua modificação ou seu traslado não provoque alterações substanciais nesses elementos, tais como semáforos, postes de sinalização e similares, terminais e pontos de acesso coletivo às telecomunicações, fontes de água, lixeiras, toldos, marquises, bancos, quiosques e quaisquer outros de natureza análoga;"),
("T31", L10257, "art. 41, § 3º", "calçadas", VIA + "113",
 "As cidades de que trata o caput deste artigo devem elaborar plano de rotas acessíveis, compatível com o plano diretor no qual está inserido, que disponha sobre os passeios públicos a serem implantados ou reformados pelo poder público, com vistas a garantir acessibilidade da pessoa com deficiência ou com mobilidade reduzida a todas as rotas e vias existentes, inclusive as que concentrem os focos geradores de maior circulação de pedestres, como os órgãos públicos e os locais de prestação de serviços públicos e privados de saúde, educação, assistência social, esporte, cultura, correios e telégrafos, bancos, entre outros, sempre que possível de maneira integrada com os sistemas de transporte coletivo de passageiros."),
("T32", L12587, "art. 12-B, caput", "táxi", VIA + "119",
 "Na outorga de exploração de serviço de táxi, reservar-se-ão 10% (dez por cento) das vagas para condutores com deficiência."),
]


def main():
    raiz = Path(__file__).parent
    linhas = []
    for id_, norma, ref, tema, obs, texto in T:
        origem = "Lei 13.146/2015" if norma == LBI else f"{norma} ({obs})"
        linhas.append({
            "id": id_, "fonte": f"{norma}, {ref}", "norma": norma, "tema": tema,
            "texto": texto, "url": URL_LBI, "origem_texto": origem,
            "licenca": "Domínio público (Lei 9.610/1998, art. 8º, IV)",
        })
    with open(raiz / "trechos.jsonl", "w", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    cont = collections.Counter(l["norma"] for l in linhas)
    md = ["| Fonte | Formato | Licença | Nº de trechos |", "|---|---|---|---|"]
    for norma, n in cont.items():
        md.append(f"| {norma} | Texto de lei (HTML/PDF oficial) → JSONL | Domínio público (Lei 9.610/98, art. 8º, IV) | {n} |")
    md.append(f"| **Total** | | | **{len(linhas)}** |")
    md.append("")
    md.append(f"Texto obtido em: {URL_COPIA}")
    md.append(f"Texto oficial: {URL_LBI}")
    (raiz / "FONTES.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(linhas)} trechos gravados")


if __name__ == "__main__":
    main()
