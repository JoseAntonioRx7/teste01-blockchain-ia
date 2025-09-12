package main

import (
	"fmt"
	"log"
	"net/http"
	"project-blockchain-ai-golang/blockchain"
	"strconv"
	"encoding/json"
)

var myBlockchain *blockchain.BlockChain

type Transaction struct {

	From    	string 		`json:"from"`
	To      	string 		`json:"to"`
	Amount  	int    		`json:"amount"`

}

type BlockResponse struct {

	Hash			string			`json:"hash"`
	Data			Transaction		`json:"data"`
	PrevHash		string			`json:"prevhash"`
	Nonce			int				`json:"nonce"`

}

type Message struct {
	Data string `json:"data"`

}

func handleGetBlocks(w http.ResponseWriter, r *http.Request) {
	var blocks []BlockResponse
	for _, block := range myBlockchain.Blocks {
		var tx Transaction
		json.Unmarshal(block.Data, &tx)

		blocks = append(blocks, BlockResponse{

			Hash:			fmt.Sprintf("%x", block.Hash),
			Data:		 	tx,
			PrevHash:		fmt.Sprintf("%x", block.PrevHash),
			Nonce:			block.Nonce,
			
		})	

	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(blocks)

}

func handlePostBlock(w http.ResponseWriter, r *http.Request) {
	var tx Transaction
	err := json.NewDecoder(r.Body).Decode(&tx)
	if err != nil || tx.From == "" || tx.To == "" || tx.Amount <= 0 {
		http.Error(w, "Transaçao Invalida", http.StatusBadRequest)
		return
	}
	myBlockchain.AddBlock(blockchain.Transactions(tx))
	w.WriteHeader(http.StatusCreated)
}

func main() {

myBlockchain := blockchain.InitBlockChain()
	
myBlockchain.AddBlock(blockchain.Transactions {
	From:    	"Sistema",
	To:      	"Primeiro bloco depois do Gênesis",
	Amount:  	50,
	
})

myBlockchain.AddBlock(blockchain.Transactions {
	From:    "Sistema",
	To:      "Segundo bloco depois do Gênesis",
	Amount:  50,
})

myBlockchain.AddBlock(blockchain.Transactions {
	From:    "Sistema",
	To:      "Terceiro bloco depois do Gênesis",
	Amount:  30,
})

	for _, block := range myBlockchain.Blocks {
		fmt.Printf("Previous Hash: %x\n", block.PrevHash)
		fmt.Printf("Data in Block: %s\n", block.Data)
		fmt.Printf("Hash: %x\n", block.Hash)

		pow := blockchain.NewProof(block)
		fmt.Printf("PoW: %s\n", strconv.FormatBool(pow.Validate()))
		fmt.Println()
	}

	http.HandleFunc("/blocks", handleGetBlocks)
	http.HandleFunc("/mine", handlePostBlock)

	fmt.Println("Servidor API iniciado em http://localhost:8080")
	fmt.Println("Blockchain válida?", myBlockchain.IsValid())
	log.Fatal(http.ListenAndServe(":8080", nil))
	
}