package main

import (
	"bytes"
	"fmt"
	"log"
	"math"
	"os"
	"regexp"
	"sort"
	"strings"

	"github.com/urfave/cli"
)

//https://gobyexample.com/reading-files

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func getNumHexDigits(num int64) int {
	i := 1
	for ; math.Pow(16, float64(i)) < float64(num); i++ {
	}
	if i%2 > 0 {
		return i + 1
	}
	return i
}

func printHexDumpLine(addressFormatString string, blocksize int, address int64, buffer []byte) {
	var stringBuffer bytes.Buffer
	var counter int
	hexAddress := fmt.Sprintf(addressFormatString, address)

	for counter = 0; counter < len(buffer); counter++ {
		stringBuffer.WriteString(fmt.Sprintf("%02x ", buffer[counter]))
		if counter%8 == 7 {
			stringBuffer.WriteString(" ")
		}
	}
	if counter < blocksize {
		stringBuffer.WriteString(strings.Repeat(" ", (blocksize-len(buffer))*3+(blocksize/8-len(buffer)/8)))
	}

	re := regexp.MustCompile("[^ -~]")
	printableString := re.ReplaceAllString(string(buffer), ".")

	fmt.Printf("0x%s:\t%s %s\n", hexAddress, stringBuffer.String(), printableString)
}

func main() {

	app := cli.NewApp()
	app.Name = "hexdump"
	app.Usage = "dumps any file or stdin as a classic hexdump"
	app.Email = "gentoomaniac@gmail.com"
	app.Version = "0.1.0"

	app.Flags = []cli.Flag{
		cli.Int64Flag{
			Name:  "number-blocks,  n",
			Value: 0,
			Usage: "dump only the given number of blocks (a block as defined by --blocksize)",
		},
		cli.Int64Flag{
			Name:  "offset, o",
			Value: 0,
			Usage: "seek the given number of bytes into the file",
		},
		cli.IntFlag{
			Name:  "blocksize, b",
			Value: 16,
			Usage: "number of bytes per row. Must be a multiple of 8",
		},
	}

	app.Action = func(c *cli.Context) error {
		var err error
		var numBytes int
		var allBytes int64
		var blocksize = c.Int("blocksize")
		var offset = c.Int64("offset")
		var numberBlocks = c.Int64("number-blocks")

		if blocksize%8 != 0 || blocksize == 0 {
			return cli.NewExitError("blocksize is not a multiple of 8", 8)
		}
		buffer := make([]byte, blocksize)

		f, err := os.Open(c.Args().Get(0))
		if err != nil {
			return err
		}
		fi, err := f.Stat()
		if err != nil {
			return err
		}
		fileSize := fi.Size()
		numHexDigits := getNumHexDigits(fileSize)
		addressFormatString := fmt.Sprintf("%%0%dx", numHexDigits)

		if offset >= fileSize {
			return cli.NewExitError("offset is larger than filesize", 16)
		}

		allBytes, err = f.Seek(offset, 0)
		if err != nil {
			return err
		}

		for err == nil {
			numBytes, err = f.Read(buffer)

			printHexDumpLine(addressFormatString, blocksize, allBytes, buffer[0:numBytes])
			allBytes += int64(numBytes)
			if numBytes < blocksize {
				break
			}
			if numberBlocks > 0 && allBytes >= offset+numberBlocks*int64(blocksize) {
				break
			}
		}

		f.Close()
		return err
	}

	sort.Sort(cli.FlagsByName(app.Flags))
	sort.Sort(cli.CommandsByName(app.Commands))

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
