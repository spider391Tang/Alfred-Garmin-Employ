<?php

require_once('workflows.php');
$w = new Workflows();
$query = trim($argv[1]);
// echo "<p> query is: ".$query."</p>";

$url = "http://biz.garmin.com.tw/introduction/index_tw.asp";
$post_data['cboEmpID1'] = $query;
$fields = array
    ( 
        CURLOPT_POSTFIELDS => "WorkType=5&cboEmpID1=$query",
        CURLOPT_COOKIE => "PassportEmpID=12001; utag_main=_st:1428654950024$ses_id:1428653893960%3Bexp-session; _ga=GA1.3.1341607043.1428653150; ASPSESSIONIDCSBDSAAS=BPKPAILDNFNLGHNPHCLKFJJE; BIGipServerQS9000_pool=167804938.20480.0000; ASPSESSIONIDCSBCTAAS=EMPBPDIAHPMKHPGEGPCDFGIN; ASPSESSIONIDCQTSABQB=JAOPNDIAJCCPJPKFPFIFMJOA"
    );
$weather = $w->request( $url, $fields );


// $findme = '分機號碼';
// $pos = strpos($weather, $findme);
// 
// if ($pos === false) {
//     echo "The string '$findme' was not found in the string";
// } else {
//     echo "The string '$findme' was found in the string";
//     echo " and exists at position $pos";
// }

preg_match('/分機號碼...([0-9]+)/', $weather, $matches);
// echo "number is : ".$matches[1]; 


	//uasort( $w->results(), 'date_sort' );
$w->result( 'employId', $query, $matches[1], '', 'icon.png', 'yes', 'autocomplete' );
echo $w->toxml();
