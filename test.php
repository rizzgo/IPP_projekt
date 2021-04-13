<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>IPP - testy</title>
</head>
<body>

<h1>Výsledky testov projektu IPP</h1>

<?php


// functions ----

/*
 Runs one test with name from .src file
 
 parameters:
 $src_file data about tested file with .src extension
 $args data about arguments
 $dir_output output data from tested directory
 */ 
function run_int_test(&$src_file, array &$args) : bool {
    $test_name = $src_file->getBasename('.src');
    $dir_path = $src_file->getPath();
    $no_extension_path = $dir_path . '/' . $test_name;

    $exit_code = -1;
    $diff_exit_code = -1;
    $out = null;
    $ref_exit_code = "";
    
    $input_path = $no_extension_path . '.in';
    $ref_output_path = $no_extension_path . '.out';
    $ref_exit_code_path = $no_extension_path . '.rc';
    $source_path = $no_extension_path . '.src';
    
    if (!is_file($input_path)) {
        $in = fopen($input_path, "w") or die("Unable to open file!");
        fclose($in);
    }
    if (!is_file($ref_output_path)) {
        $out = fopen($ref_output_path, "w") or die("Unable to open file!");
        fclose($out);
    }
    if (!is_file($ref_exit_code_path)) {
        $rc = fopen($ref_exit_code_path, "w") or die("Unable to open file!");
        fwrite($rc, "0");
        fclose($rc);
    }

    $ref_exit_code = file_get_contents($ref_exit_code_path);

    exec('python3.8 ' . $args['interpret_path'] . ' --source=' . $source_path . ' --input=' . $input_path . ' > tmp.out', $out, $exit_code);
    if ($ref_exit_code == $exit_code) {
        if ($exit_code == 0) {
            exec('diff' . ' tmp.out ' . $ref_output_path, $out, $diff_exit_code);
            if ($diff_exit_code == 0) {
                return true;
            }
            else {
                echo "<h4>" . $no_extension_path ." | invalid output</h4>\n";
                return false;
            }
        }
        else {
            return true;
        }
    }
    echo "<h4>" . $no_extension_path ." | exit code: ".$exit_code." valid: ".$ref_exit_code; "</h4>\n";
    return false;
}

/*
 Runs one test with name from .src file
 
 parameters:
 $src_file data about tested file with .src extension
 $args data about arguments
 $dir_output output data from tested directory
 */ 
function run_parser_test(&$src_file, array &$args) : bool {
    $test_name = $src_file->getBasename('.src');
    $dir_path = $src_file->getPath();
    $no_extension_path = $dir_path . '/' . $test_name;

    $exit_code = -1;
    $xml_exit_code = -1;
    $out = null;
    $test_arguments = ""; 
    $ref_exit_code = "";

    $input_path = $no_extension_path . '.in';
    $ref_output_path = $no_extension_path . '.out';
    $ref_exit_code_path = $no_extension_path . '.rc';
    $source_path = $no_extension_path . '.src'; 
  
    if (!is_file($input_path)) {
        $in = fopen($input_path, "w") or die("Unable to open file!");
        fclose($in);
    }
    if (!is_file($ref_output_path)) {
        $out = fopen($ref_output_path, "w") or die("Unable to open file!");
        fclose($out);
    }
    if (!is_file($ref_exit_code_path)) {
        $rc = fopen($ref_exit_code_path, "w") or die("Unable to open file!");
        fwrite($rc, "0");
        fclose($rc);
    }

    $test_arguments = file_get_contents($input_path);
    $ref_exit_code = file_get_contents($ref_exit_code_path);

    exec('php7.4 ' . $args['parser_path'] . $test_arguments . ' < ' . $source_path . ' > tmp.out', $out, $exit_code);
    if ($ref_exit_code == $exit_code) {
        if ($exit_code == 0) {
            exec('java -jar ' . $args['jexam_path'] . ' tmp.out ' . $ref_output_path .
                ' difffile.xml ' . $args['jexam_opt_path'], $out, $xml_exit_code);
            if ($xml_exit_code == 0) { // TODO - A7Soft JExamXML - done
                return true;
            }
        }
        else {
            return true;
        }
    }
    echo "<h4>" . $no_extension_path . "</h4>\n";
    return false;
}

/*
 Looks for tests in tested directory from $args.
 With script argument --recursive searches recursively.
 
 parameters:
 $args data about arguments
 $dir_output output data from tested directory
 */
function search_directory(array &$args) {
    $test_elements = new FileSystemIterator($args['tests_path']);
    $tests = 0;
    $passed = 0;
    echo "<h2>" . $args['tests_path'] . "</h2>\n";
    foreach ($test_elements as $element_path => $element) {
        if ($element->isDir() && $args['recursive']) {
            $args['tests_path'] = $element_path;
            search_directory($args);
        }
        else {
            if ($element->getExtension() == 'src') {
                switch ($args['test_suite']) {
                    case "all":
                        break;
                    case "parse":
                        if(run_parser_test($element, $args)) $passed++;
                        break;
                    case "int":
                        if(run_int_test($element, $args)) $passed++;
                        break;
                    default:
                        break;
                }
                $tests++;
            }
        }
    }
    echo "<p>\n";
    echo "---------------------------------------------<br>\n";
    echo "tests: " . $tests . "<br>\n";
    echo "passed: " . $passed . "\n";
    echo "</p>\n";
}

/*
 Sets and controls everything before testing

 parameters:
 $args data about arguments
 $arg_flags data about used script arguments
 $output_data output data from all directories
 */
function run_testing(array &$args, array &$arg_flags) {
    if (($arg_flags['parse_only'] && $arg_flags['int_active']) || ($arg_flags['int_only'] && $arg_flags['parse_active'])) {
        exit(41);
    }

    switch ($args['test_suite']) {
        case "all":
            break;
        case "parse":
            $args['tests_path'] = preg_replace("#/$#", "", $args['tests_path']);
            $args['tests_path'] = preg_replace("#$#", "/parse-only", $args['tests_path']);
            break;
        case "int":
            $args['tests_path'] = preg_replace("#/$#", "", $args['tests_path']);
            $args['tests_path'] = preg_replace("#$#", "/interpret-only", $args['tests_path']);
            break;
        default:
            exit(41);
    }
    if (is_dir($args['tests_path'])) {
        search_directory($args);
    }
    else exit(41);
}


// setting default arguments ----
$args = array(
    'recursive' => false,
    'test_suite' => "all",
    'tests_path' => getcwd(), // 'testfolder/ipp-2020-tests'
    'parser_path' => 'parse.php',
    'interpret_path' => 'interpret.py',
    'jexam_path' => '/pub/courses/ipp/jexamxml/jexamxml.jar', // 'wisfiles/jexam/jexamxml.jar'
    'jexam_opt_path' => '/pub/courses/ipp/jexamxml/options', // 'wisfiles/jexam/options'
);

// reading arguments ----
$arg_counter = $argc;
$arg_flags = array(
    'parse_active' => false,
    'int_active' => false,
    'parse_only' => false,
    'int_only' => false,
);
while ($arg_counter > 1) {
    $arg_actual = $arg_counter - 1;
    if ($argc == 2 && preg_match("/^--help$/", $argv[$arg_actual])) {
        echo <<<HELP

        Skript test.php slouzi pro automaticke testovani aplikace parse.php a interpret.py. Skript projde 
        zadany adresar s testy a vyuzije je pro automaticke otestovani spravne funkcnosti jednoho ci obou 
        predchozich skriptu vcetne vygenerovani prehledneho souhrnu v HTML 5 na standardni vystup. 
        

        --help  
                        Vypise na standardni vystup napovedu skriptu (nenacita zadni vstup).
                        
        --directory=path  
                        Testy bude hledat v zadanem adresari (chybi-li tento parametr, 
                        tak skript prochazi aktualni adresar).
                        
        --recursive  
                        Testy bude hledat nejen v zadanem adresari, ale i rekurzivne ve vsech 
                        jeho podadresarich.
                        
        --parse-script=file  
                        Soubor se skriptem v PHP 7.4 pro analyzu zdrojoveho kodu 
                        v IPPcode21 (chybi-li tento parametr, tak implicitni hodnotou je parse.php 
                        ulozeny v aktualnim adresari).
                        
        --int-script=file  
                        Soubor se skriptem v Python 3.8 pro interpret XML reprezentace kodu
                        v IPPcode21 (chybi-li tento parametr, tak implicitni hodnotou je interpret.py ulozeny
                        v aktualnim adresari).
                        
        --parse-only  
                        Bude testovan pouze skript pro analyzu zdrojoveho kodu v IPPcode21 (tento
                        parametr se nesmi kombinovat s parametry --int-only a --int-script), vystup s referencnim
                        vystupem (soubor s priponou out) porovnavejte nastrojem A7Soft JExamXML (viz [2]).
                        
        --int-only  
                        Bude testovan pouze skript pro interpret XML reprezentace kodu v IPPcode21
                        (tento parametr se nesmi kombinovat s parametry --parse-only a --parse-script). Vstupni
                        program reprezentovan pomoci XML bude v souboru s priponou src.
                        
        --jexamxml=file  
                        Soubor s JAR balickem s nastrojem A7Soft JExamXML. Je-li parametr
                        vynechan uvazuje se implicitni umisteni /pub/courses/ipp/jexamxml/jexamxml.jar na serveru 
                        Merlin, kde bude test.php hodnocen.
                        
        --jexamcfg=file  
                        Soubor s konfiguraci nastroje A7Soft JExamXML. Je-li parametr vynechan
                        uvazuje se implicitni umisteni /pub/courses/ipp/jexamxml/options na serveru Merlin, kde
                        bude test.php hodnocen.

        \n
        HELP;
        exit(0);
    }
    elseif (preg_match("/^--directory=/", $argv[$arg_actual])) {
        $args['tests_path'] = preg_replace("/^--directory=/", "", $argv[$arg_actual]);
    }
    elseif (preg_match("/^--recursive$/", $argv[$arg_actual])) {
        $args['recursive'] = true;
    }
    elseif (preg_match("/^--parse-script=/", $argv[$arg_actual])) {
        $args['parser_path'] = preg_replace("/^--parse-script=/", "", $argv[$arg_actual]);
        $arg_flags['parse_active'] = true;
    }
    elseif (preg_match("/^--int-script=/", $argv[$arg_actual])) {
        $args['interpret_path'] = preg_replace("/^--int-script=/", "", $argv[$arg_actual]);
        $arg_flags['int_active'] = true;
    }
    elseif (preg_match("/^--parse-only$/", $argv[$arg_actual])) {
        $args['test_suite'] = "parse";
        $arg_flags['parse_active'] = true;
        $arg_flags['parse_only'] = true;
    }
    elseif (preg_match("/^--int-only$/", $argv[$arg_actual])) {
        $args['test_suite'] = "int";
        $arg_flags['int_active'] = true;
        $arg_flags['int_only'] = true;
    }
    elseif (preg_match("/^--jexamxml=/", $argv[$arg_actual])) {
        $args['jexam_path'] = preg_replace("/^--jexamxml=/", "", $argv[$arg_actual]);
    }
    elseif (preg_match("/^--jexamcfg=/", $argv[$arg_actual])) {
        $args['jexam_opt_path'] = preg_replace("/^--jexamcfg=/", "", $argv[$arg_actual]);
    }
    else exit(10);

    $arg_counter--;
}

// testing and saving output ----

run_testing($args, $arg_flags);
?>


</body>
</html>