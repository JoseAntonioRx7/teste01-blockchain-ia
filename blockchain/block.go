package blockchain

import(
	"encoding/json"
	"log"
)

 type BlockChain struct{
	Blocks []*Block
}

type Block struct{

	Hash		[] byte
	Data		[] byte
	PrevHash	[] byte
	Nonce		int

}

func CreateBlock(tx Transactions, prevHash []byte) *Block {
	data, err := json.Marshal(tx)
	if err != nil {
		log.Panic(err)
	}

	block := &Block{[]byte{}, data, prevHash, 0}
	pow := NewProof(block)
	nonce, hash := pow.Run()

	block.Hash = hash[:]
	block.Nonce = nonce

	return block
}

func (chain *BlockChain) AddBlock(tx Transactions) {
	prevBlock := chain.Blocks[len(chain.Blocks)-1]
	new := CreateBlock(tx, prevBlock.Hash)
	chain.Blocks = append(chain.Blocks, new)
}

func Genesis() *Block {
	return CreateBlock(Transactions{
		From:   "Sistema",
		To:     "Gênesis",
		Amount: 0,
	}, []byte{})
}

func InitBlockChain() *BlockChain{
	return &BlockChain{[]*Block{Genesis()}}
}

func (bc *BlockChain) IsValid() bool {
	for i := 1; i < len(bc.Blocks); i++ {
		current := bc.Blocks[i]
		previous := bc.Blocks[i-1]

		if string(current.PrevHash) != string(previous.Hash) {
			return false
		}

		pow := NewProof(current)
		if !pow.Validate() {
			return false
		}
	}
	return true
}

type Transactions struct {
	From    	string `json:"from"`
	To      	string `json:"to"`
	Amount  	int    `json:"amount"`

}