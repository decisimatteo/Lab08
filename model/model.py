from database.distributore_DAO import DistributoreDAO

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        if not 1 <= mese <= 12:
            raise ValueError("Il mese deve essere compreso tra 1 e 12.")

        if self._distributori is None:
            self.load_distributori()
        if self._distributori is None or len(self._distributori) == 0:
            raise Exception("Impossibile leggere i distributori. Controlla MySQL e il database.")

        medie = []
        for distributore in self._distributori:
            prezzi = distributore.get_prezzi()
            if prezzi is None:
                raise Exception(f"Impossibile leggere i prezzi di {distributore.nome}.")

            somma = 0
            numero_prezzi = 0
            for prezzo in prezzi:
                if prezzo.data.year == 2026 and prezzo.data.month == mese:
                    somma += prezzo.prezzo_litro
                    numero_prezzi += 1

            if numero_prezzi == 0:
                raise Exception(f"Nessun prezzo presente nel mese scelto per {distributore.nome}.")

            medie.append((distributore.nome, somma / numero_prezzi))

        return medie

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        if giorno == 8:
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                # Copio la lista, così i successivi pop() non cambiano la soluzione salvata
                self.__sequenza_ottima = sequenza_parziale[:]
            return

        for id_distributore in prezzi_settimana:
            costo_giorno = prezzi_settimana[id_distributore][giorno - 1] * 100

            # Il primo giorno non c'è un distributore precedente da cui spostarsi
            if ultimo_distributore is not None and ultimo_distributore != id_distributore:
                costo_giorno += 5

            sequenza_parziale.append(id_distributore)
            self.__ricorsione(sequenza_parziale, giorno + 1, id_distributore,
                             costo_corrente + costo_giorno, prezzi_settimana)
            # Tolgo l'ultima scelta per provare l'altro distributore nello stesso giorno
            sequenza_parziale.pop()

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        if not 1 <= mese <= 12:
            raise ValueError("Il mese deve essere compreso tra 1 e 12.")

        if self._distributori is None:
            self.load_distributori()
        if self._distributori is None or len(self._distributori) == 0:
            raise Exception("Impossibile leggere i distributori. Controlla MySQL e il database.")

        prezzi_settimana = {}
        for distributore in self._distributori:
            prezzi = distributore.get_prezzi()
            if prezzi is None:
                raise Exception(f"Impossibile leggere i prezzi di {distributore.nome}.")

            prezzi_giorni = [None] * 7
            for prezzo in prezzi:
                if prezzo.data.year == 2026 and prezzo.data.month == mese and 1 <= prezzo.data.day <= 7:
                    # Uso il giorno come posizione, anche se il database restituisce i dati fuori ordine
                    prezzi_giorni[prezzo.data.day - 1] = prezzo.prezzo_litro

            if None in prezzi_giorni:
                raise Exception(f"Mancano dei prezzi nei primi 7 giorni per {distributore.nome}.")

            prezzi_settimana[distributore.id] = prezzi_giorni

        return prezzi_settimana
