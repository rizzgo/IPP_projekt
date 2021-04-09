<?php 


// functions ----

/*
 Replaces special characters in $word with xml versions
 */
function replace_special_to_xml(string $word) : string {
    $xmlword = preg_replace("/&/", "&amp;", $word);
    $xmlword = preg_replace("/</", "&lt;", $xmlword);
    $xmlword = preg_replace("/>/", "&gt;", $xmlword);
    $xmlword = preg_replace("/\"/", "&quot;", $xmlword);
    $xmlword = preg_replace("/\'/", "&apos;", $xmlword);
    return $xmlword;
}

/*
 Moves to next token in semantic analysis
 
 parameters:
 $tokens data about all tokens
 */
function get_next_token(array &$tokens_struct) {
    $tokens_struct["num"]++;
    $tokens_struct["act"] = $tokens_struct["arr"][$tokens_struct["num"]];
}



// write errors to stderr ----

ini_set('display_errors', 'stderr');


// help argument ----

if ($argc > 1) {
    if ($argc == 2 && $argv[1] = "--help") {
        echo <<<HELP

        Skript parse.php nacte ze standardniho vstupu zdrojovy kod v IPPcode21,
        zkontroluje lexikalni a syntaktickou spravnost kodu a vypise na standardni
        vystup XML reprezentaci programu.
        
        --help  
                Vypise na standardni vystup napovedu skriptu (nenacita zadni vstup).

        \n
        HELP;
        exit(0);
    }
    else exit(10);
}


// clean input ----

$inputfile = stream_get_contents(STDIN);
$withoutcomments = preg_replace("/#.*/", "", $inputfile);
$cleanbeforeheader = preg_replace("/^\n+/", "", $withoutcomments);
$explicitnewlines = preg_replace("/\n+/", " @newline@ ", $cleanbeforeheader);
$words = preg_split('/[\s]+/', $explicitnewlines, -1, PREG_SPLIT_NO_EMPTY);


// tokens creation (lexical analysis) -----------------------------

$tokens = array();

if (!empty($words) && !preg_match("/^.IPPcode21$/i", $words[0])) {
    exit(21);
}

foreach ($words as $word) {
    if (preg_match("/^.IPPcode21$/i", $word)) {
        $token = array("head", $word);
        array_push($tokens, $token);
    }
    elseif (preg_match("/^@newline@$/", $word)) {
        $token = array("newline", $word);
        array_push($tokens, $token);
    }
    elseif (preg_match("/^([a-z]|[A-Z]|[0-9])+$/", $word)) {

        if (preg_match("/^(int|string|bool)$/", $word)) {
            $token = array("type", $word);
            array_push($tokens, $token);
        }
        elseif (preg_match("/^(MOVE|CREATEFRAME|PUSHFRAME|POPFRAME|DEFVAR|CALL|RETURN|(
        ){0}PUSHS|POPS|ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|NOT|INT2CHAR|STRI2INT|READ|(
        ){0}WRITE|CONCAT|STRLEN|GETCHAR|SETCHAR|TYPE|LABEL|JUMP|JUMPIFEQ|JUMPIFNEQ|(
        ){0}EXIT|DPRINT|BREAK)$/i", $word)) {  // (\n){0} in regex ignores new line 
            $token = array("inst", strtoupper($word), $word);
            array_push($tokens, $token);
        }
        else {
            $token = array("label", $word);
            array_push($tokens, $token);
        }
    }
    elseif (preg_match("/^([a-z]|[A-Z]|[_\-$&%*!?])([a-z]|[A-Z]|[0-9]|[_\-$&%*!?])*$/", $word)) {
        $xmlword = replace_special_to_xml($word);
        $token = array("label", $xmlword);
        array_push($tokens, $token);
    }
    elseif (preg_match("/^(LF|TF|GF)@([a-z]|[A-Z]|[_\-$&%*!?])([a-z]|[A-Z]|[0-9]|[_\-$&%*!?])*$/", $word)) {
        $xmlword = replace_special_to_xml($word);
        $token = array("var", $xmlword);
        array_push($tokens, $token);   
    }
    elseif (preg_match("/^nil@nil$/", $word)) {
        $token = array("nil", preg_replace("/^nil@/", "", $word));
        array_push($tokens, $token);   
    }
    elseif (preg_match("/^bool@(true|false)$/", $word)) {
        $token = array("bool", preg_replace("/^bool@/", "", $word));
        array_push($tokens, $token);   
    }
    elseif (preg_match("/^int@[-+]?[0-9]+$/", $word)) {
        $token = array("int", preg_replace("/^int@/", "", $word));
        array_push($tokens, $token);   
    }
    elseif (preg_match("/^string@([^\s#\\\]|(\\\[0-9]{3}))*$/", $word)) {
        $xmlword = replace_special_to_xml($word);
        $token = array("string", preg_replace("/^string@/", "", $xmlword));
        array_push($tokens, $token);   
    }
    else exit(23);
}


// append end of file ----

$token = array("EOF", "eof");
array_push($tokens, $token);


// tokens structure creation ----

$tokens_struct = array("inst_num" => 0 , "num" => 0, "act" => $tokens[0], "arr" => $tokens);


// parsing (syntactic analysis) functions ---------------------------

// runs syntactic analysis
function syntactic_analysis(array &$tokens_struct, &$xml) : bool {
    return program($tokens_struct, $xml);
}

// checks whole program
function program(array &$tokens_struct, &$xml) : bool {
    if (head($tokens_struct, $xml)) {
        header("content-type: application/xml; charset=UTF-8");
        $xml_program = $xml->createElement("program");
        $xml_program->setAttribute("language", "IPPcode21");
        $xml->appendChild($xml_program);
        if (inst_next($tokens_struct, $xml)) {
            $xml->formatOutput = True;
            print $xml->saveXML();
            return true;
        }
    }
    return false;
}

// checks program header
function head(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "head") == 0) {
        get_next_token($tokens_struct);
        return true;
    }
    exit(21);
}

// checks all instructions
function insts(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "inst") == 0) {
        if (inst($tokens_struct, $xml)) {
            if (inst_next($tokens_struct, $xml)) {
                return true;
            }
        }
        return false;
    }
    elseif (strcmp($tokens_struct["act"][0], "EOF") == 0) {
        return true;
    }
    exit(22);

}

// checks one instruction
function inst(array &$tokens_struct, &$xml) : bool {
    $tokens_struct["inst_num"]++;

    $xml_instruction = $xml->createElement("instruction");
    $xml_instruction->setAttribute("order", $tokens_struct["inst_num"]);
    $xml_instruction->setAttribute("opcode", $tokens_struct["act"][1]);
    $xml_program = $xml->getElementsByTagName("program");
    $xml_program[0]->appendChild($xml_instruction);
    
    if (in_array(strtolower($tokens_struct["act"][1]), array("add", "sub", "mul", "idiv", "lt", "gt", "eq", "and",
                                        "or", "stri2int", "concat", "getchar", "setchar"))) {
        get_next_token($tokens_struct);
        return var1symb2($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("move", "not", "int2char", "strlen", "type"))) {
        get_next_token($tokens_struct);
        return var1symb1($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("jumpifeq", "jumpifneq"))) {
        get_next_token($tokens_struct);
        return label1symb2($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("read"))) {
        get_next_token($tokens_struct);
        return var1type1($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("defvar", "pops"))) {
        get_next_token($tokens_struct);
        return var1($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("call", "label", "jump"))) {
        get_next_token($tokens_struct);
        return label1($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("pushs", "write", "exit", "dprint"))) {
        get_next_token($tokens_struct);
        return symb1($tokens_struct, $xml);
    }
    elseif (in_array(strtolower($tokens_struct["act"][1]), array("createframe", "pushframe", "popframe", "return", "break"))) {
        get_next_token($tokens_struct);
        return empty1($tokens_struct, $xml);
    }
    return false;
}

// connection to the next instruction
function inst_next(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "newline") == 0) {
        get_next_token($tokens_struct);
        if (insts($tokens_struct, $xml)) {
            return true;
        }
    }
    elseif (strcmp($tokens_struct["act"][0], "EOF") == 0) {
        return true;
    }
    return false;

}

// checks symbol
function symb(array &$tokens_struct, &$xml) : bool {
    if (in_array($tokens_struct["act"][0], array("nil", "bool", "int", "string", "var"))) {
        return true;
    }
    return false;
}

// checks label and does conversion
function label(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "label") == 0) {
        return true;
    } 
    elseif (strcmp($tokens_struct["act"][0], "type") == 0) { // converting type to label
        $tokens_struct["arr"][$tokens_struct["num"]][0] = "label";
        $tokens_struct["act"] = $tokens_struct["arr"][$tokens_struct["num"]];
        return true;
    }
    elseif (strcmp($tokens_struct["act"][0], "inst") == 0) { // converting instruction to label
        $tokens_struct["arr"][$tokens_struct["num"]][0] = "label"; // (uppercase to previous)
        $tokens_struct["arr"][$tokens_struct["num"]][1] = $tokens_struct["arr"][$tokens_struct["num"]][2];
        $tokens_struct["act"] = $tokens_struct["arr"][$tokens_struct["num"]];
        return true;
    }
    return false;
}

// checks instruction with one variable and two symbols
function var1symb2(array &$tokens_struct, &$xml) : bool {    
    if (strcmp($tokens_struct["act"][0], "var") == 0) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        get_next_token($tokens_struct);
        if (symb($tokens_struct, $xml)) {

            $xml_arg2 = $xml->createElement("arg2");
            $xml_arg2->setAttribute("type", $tokens_struct["act"][0]);
            $xml_arg2->nodeValue = $tokens_struct["act"][1];         
            
            get_next_token($tokens_struct);
            if (symb($tokens_struct, $xml)) {
                
                $xml_arg3 = $xml->createElement("arg3");
                $xml_arg3->setAttribute("type", $tokens_struct["act"][0]);
                $xml_arg3->nodeValue = $tokens_struct["act"][1]; 

                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg2);
                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg3);
        
                get_next_token($tokens_struct);
                return true;
            }   
        }
    }
    return false;
}

// checks instruction with one variable and one symbol
function var1symb1(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "var") == 0) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        get_next_token($tokens_struct);
        if (symb($tokens_struct, $xml)) {

            $xml_arg2 = $xml->createElement("arg2");
            $xml_arg2->setAttribute("type", $tokens_struct["act"][0]);
            $xml_arg2->nodeValue = $tokens_struct["act"][1];         
            
            $xml_instruction = $xml->getElementsByTagName("instruction");
            $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
            $xml_instruction = $xml->getElementsByTagName("instruction");
            $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg2);
    
            get_next_token($tokens_struct);
            return true;
        }
    }
    return false;
}

// checks instruction with one label and two symbols
function label1symb2(array &$tokens_struct, &$xml) : bool {
    if (label($tokens_struct, $xml)) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        get_next_token($tokens_struct);
        if (symb($tokens_struct, $xml)) {

            $xml_arg2 = $xml->createElement("arg2");
            $xml_arg2->setAttribute("type", $tokens_struct["act"][0]);
            $xml_arg2->nodeValue = $tokens_struct["act"][1];         

            get_next_token($tokens_struct);
            if (symb($tokens_struct, $xml)) {

                $xml_arg3 = $xml->createElement("arg3");
                $xml_arg3->setAttribute("type", $tokens_struct["act"][0]);
                $xml_arg3->nodeValue = $tokens_struct["act"][1]; 

                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg2);
                $xml_instruction = $xml->getElementsByTagName("instruction");
                $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg3);
        
                get_next_token($tokens_struct);
                return true;
            }   
        }
    }
    return false;
}

// checks instruction with one variable and one type
function var1type1(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "var") == 0) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        get_next_token($tokens_struct);
        if (strcmp($tokens_struct["act"][0], "type") == 0) {

            $xml_arg2 = $xml->createElement("arg2");
            $xml_arg2->setAttribute("type", $tokens_struct["act"][0]);
            $xml_arg2->nodeValue = $tokens_struct["act"][1];         

            $xml_instruction = $xml->getElementsByTagName("instruction");
            $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
            $xml_instruction = $xml->getElementsByTagName("instruction");
            $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg2);
    
            get_next_token($tokens_struct);
            return true;
        }
    }
    return false;
}

// checks instruction with only one variable
function var1(array &$tokens_struct, &$xml) : bool {
    if (strcmp($tokens_struct["act"][0], "var") == 0) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        $xml_instruction = $xml->getElementsByTagName("instruction");
        $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
    
        get_next_token($tokens_struct);
        return true;
    }
    return false;
}

// checks instruction with only one label
function label1(array &$tokens_struct, &$xml) : bool {
    if (label($tokens_struct, $xml)) {

        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        $xml_instruction = $xml->getElementsByTagName("instruction");
        $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
    
        get_next_token($tokens_struct);
        return true;
    }
    return false;
}

// checks instruction with only one symbol
function symb1(array &$tokens_struct, &$xml) : bool {
    if (symb($tokens_struct, $xml)) {
        
        $xml_arg1 = $xml->createElement("arg1");
        $xml_arg1->setAttribute("type", $tokens_struct["act"][0]);
        $xml_arg1->nodeValue = $tokens_struct["act"][1];
        
        $xml_instruction = $xml->getElementsByTagName("instruction");
        $xml_instruction[$tokens_struct["inst_num"] - 1]->appendChild($xml_arg1);
    
        get_next_token($tokens_struct);
        return true;
    }
    return false;
}

// checks instruction with no arguments
function empty1(array &$tokens_struct, &$xml) : bool {
    return true;
}


// run syntactic analysis and export to xml ------------------------------

$xml = new DOMDocument("1.0", "UTF-8");
$syntactic_analysis = syntactic_analysis($tokens_struct, $xml);
if (!$syntactic_analysis) {
    exit(23);  
}

exit(0);




?> 
