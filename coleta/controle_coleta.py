import time
import threading
from contextlib import contextmanager

from coleta.gerenciador_fontes import carregar_cadastro


class ControleColeta:

    def __init__(self):
        self.dados = carregar_cadastro()
        self.fontes = {
            fonte["id"]: fonte
            for fonte in self.dados["fontes"]
        }

        self._bloqueio_global = threading.Lock()
        self._ultima_requisicao = {}
        self._fontes_pausadas = {}

    def intervalo(self, fonte_id):
        fonte = self.fontes.get(fonte_id)

        if fonte is None:
            raise ValueError("Fonte não cadastrada: " + fonte_id)

        return fonte["intervalo_segundos"]

    def esta_pausada(self, fonte_id):
        return fonte_id in self._fontes_pausadas

    def motivo_pausa(self, fonte_id):
        return self._fontes_pausadas.get(fonte_id)

    def registrar_resultado(
        self, fonte_id, status_http=None, captcha=False
    ):
        if fonte_id not in self.fontes:
            raise ValueError("Fonte não cadastrada: " + fonte_id)

        if captcha:
            motivo = "CAPTCHA identificado"
        elif status_http in (403, 429):
            motivo = "HTTP " + str(status_http)
        else:
            return False

        self._fontes_pausadas[fonte_id] = motivo
        return True

    @contextmanager
    def requisicao(self, fonte_id):
        fonte = self.fontes.get(fonte_id)

        if fonte is None:
            raise ValueError("Fonte não cadastrada: " + fonte_id)

        if fonte["coleta_automatica"] is not True:
            raise PermissionError("Coleta automática desabilitada")

        if fonte["situacao"] != "autorizada":
            raise PermissionError("Fonte sem autorização validada")

        self._bloqueio_global.acquire()

        try:
            if self.esta_pausada(fonte_id):
                raise PermissionError(
                    "Fonte pausada: " + str(self.motivo_pausa(fonte_id))
                )

            intervalo = self.intervalo(fonte_id)
            ultima = self._ultima_requisicao.get(fonte_id)

            if ultima is not None:
                espera = intervalo - (time.monotonic() - ultima)

                if espera > 0:
                    time.sleep(espera)

            self._ultima_requisicao[fonte_id] = time.monotonic()

            yield

        finally:
            self._bloqueio_global.release()
