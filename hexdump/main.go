package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	glog "log"
	"math"
	"os"
	"regexp"
	"strings"

	"github.com/alecthomas/kong"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

var (
	version = "0.0.1-dev"
)

var cli struct {
	Verbose int  `short:"v" help:"Increase verbosity." type:"counter"`
	Quiet   bool `short:"q" help:"Do not run upgrades."`
	Json    bool `help:"Log as json"`

	Blocksize  int   `help:"number of bytes per row. Must be a multiple of 8" short:"b" default:"16"`
	NumberRows int   `help:"number of rows to print, default is all" short:"n"`
	Offset     int64 `help:"seek the given number of bytes into the file" short:"o" default:"0"`

	Filename string `help:"File to open" arg:"" optional:""`

	Version kong.VersionFlag `short:"v" help:"Display version."`
}

func setupLogging(verbosity int, logJson bool, quiet bool) {
	if !quiet {
		// 1 is zerolog.InfoLevel
		zerolog.SetGlobalLevel(zerolog.Level(1 - verbosity))
		if !logJson {
			log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})
		}
	} else {
		zerolog.SetGlobalLevel(zerolog.Disabled)
		glog.SetFlags(0)
		glog.SetOutput(ioutil.Discard)
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

func getHexDumpLine(addressFormatString string, blocksize int, address int64, buffer []byte) string {
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

	return fmt.Sprintf("0x%s:\t%s %s", hexAddress, stringBuffer.String(), printableString)
}

func main() {
	ctx := kong.Parse(&cli, kong.UsageOnError(), kong.Vars{
		"version": version,
	})
	setupLogging(cli.Verbose, cli.Json, cli.Quiet)

	if cli.Blocksize%8 != 0 || cli.Blocksize <= 0 {
		log.Error().Msg("Blocksize not devisible by 8 or <= 0")
		ctx.Exit(1)
	}
	buffer := make([]byte, cli.Blocksize)

	var err error
	var f *os.File
	addressFormatString := fmt.Sprintf("%%0%dx", 4)
	var allBytes int64
	if cli.Filename == "" {
		f = os.Stdin
		if cli.Offset != 0 {
			log.Warn().Msg("reading from stdin, ignoring --offset")
		}
	} else {
		f, err = os.Open(cli.Filename)
		if err != nil {
			log.Error().Err(err).Msg("file open failed")
			ctx.Exit(1)
		}
		fi, err := f.Stat()
		if err != nil {
			log.Error().Err(err).Msg("file stat failed")
			ctx.Exit(1)
		}
		fileSize := fi.Size()
		numHexDigits := getNumHexDigits(fileSize)
		addressFormatString = fmt.Sprintf("%%0%dx", numHexDigits)

		if cli.Offset >= fileSize {
			log.Error().Int64("filesize", fileSize).Int64("offset", cli.Offset).Msg("offset is larger than filesize")
			ctx.Exit(1)
		}

		allBytes, err = f.Seek(int64(cli.Offset), 0)
		if err != nil {
			log.Error().Err(err).Msg("Seek failed")
			ctx.Exit(1)
		}
	}

	var read int
	for err == nil {
		read, err = f.Read(buffer)

		fmt.Println(getHexDumpLine(addressFormatString, cli.Blocksize, allBytes, buffer[0:read]))
		allBytes += int64(read)
		if read < cli.Blocksize {
			break
		}
		if cli.NumberRows > 0 && allBytes >= cli.Offset+int64(cli.NumberRows)*int64(cli.Blocksize) {
			break
		}
	}

	f.Close()

	ctx.Exit(0)
}
