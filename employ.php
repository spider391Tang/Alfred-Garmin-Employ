<?php
require_once('workflows.php');
$w = new Workflows();

// Employ ID from input
$query = trim($argv[1]);



$url = "http://biz.garmin.com.tw/introduction/index_tw.asp";

// Hack to access the 'Garmin Introduction' cookie
$session_name = "ASPSESSIONIDAQTRCBRA";
$session_value = "";

$homepage = file_get_contents('/Users/spider391tang/Library/Application Support/Firefox/Profiles/8xd2azir.default/sessionstore-backups/recovery.js');
$items = json_decode( $homepage );

foreach( $items->windows[0]->cookies as $cn ):
    if ( trim( $cn->name ) == $session_name ):
        $session_value = $cn->value;
        break;
    endif;
endforeach;

// print_r( $session_value );

$fields = array
    ( 
        CURLOPT_POSTFIELDS => "WorkType=5&cboEmpID1=$query",
        CURLOPT_COOKIE => "$session_name=$session_value; BIGipServerQS9000_pool=167804938.20480.0000"
    );

$result = $w->request( $url, $fields );
// print_r( $result );
preg_match('/分機號碼...([0-9]+)/', $result, $matches_phone);
preg_match('/ORG...(.+?)<\/li>/', $result, $matches_org);
preg_match('/部門...(.+?)\s+<li>/', $result, $matches_dep);
$rtn = preg_match('/名字...<font color=blue>(.*?)<\/font>/', $result, $matches_name);

$employ_info = $matches_name[1] . " " . $matches_org[1] . " - " . $matches_phone[1] . " " . $matches_dep[1];

if( $rtn == 1 and !file_exists( "images/$query.jpg" ) ):
    // download image
    $image_url = "http://10.128.0.10/engineers/images/$query.jpg";
    $ch = curl_init( $image_url );
    $fp = fopen("images/$query.jpg", 'wb');
    curl_setopt($ch, CURLOPT_FILE, $fp);
    curl_setopt($ch, CURLOPT_HEADER, 0);
    curl_exec($ch);
    curl_close($ch);
    fclose($fp);
endif;

$w->result( 'employ', $query, $employ_info, '', "images/$query.jpg", 'yes', 'autocomplete' );
echo $w->toxml();
