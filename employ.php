<?php
require_once('workflows.php');
require_once('simple_html_dom.php');

$w = new Workflows();

// Employ info from input
$query = trim( $argv[1] );

if( strlen( $query ) < 3 )
{
    return;
}

$url = "http://biz.garmin.com.tw/introduction/index_tw.asp";

// Hack to access the 'Garmin Introduction' cookie
$host_name = "biz.garmin.com.tw";
$aspsession_prefix = "ASPSESSION";
$aspsession_name= "";
$aspsession_value= "";
$biggipserver_prefix = "BIGipServer";
$biggipserver_name = "";
$biggipserver_value = "";

$session_bak_json = file_get_contents('/Users/spider391tang/Library/Application Support/Firefox/Profiles/8xd2azir.default/sessionstore-backups/recovery.js');
$session_bak_array = json_decode( $session_bak_json );

foreach( $session_bak_array->windows as $window )
{
    $cookie_found = FALSE;
    foreach( $window->cookies as $co )
    {
        $co_host = trim( $co->host );
        $co_name = trim( $co->name );


        if( strpos( $co_host, $host_name ) !== FALSE and strpos( $co_name, $aspsession_prefix ) !== FALSE )
        {
            $aspsession_name = $co_name;
            $aspsession_value = trim( $co->value );
            $cookie_found = TRUE;
        }

        if( strpos( $co_host, $host_name ) !== FALSE and strpos( $co_name, $biggipserver_prefix ) !== FALSE )
        {
            $biggipserver_name = $co_name;
            $biggipserver_value = trim( $co->value );
            $cookie_found = TRUE;
        }
    }
    if( $cookie_found )
    {
        break;
    }
}

$query_fields = "";

if( is_numeric( $query ) )
{
    $query_fields =  "WorkType=5&cboEmpID1=$query"; 
} 
else
{
    $query_fields = "WorkType=6&cboEmpName=$query";
}

$fields = array
    ( 
        CURLOPT_POSTFIELDS => $query_fields,
        CURLOPT_COOKIE => "$aspsession_name=$aspsession_value; $biggipserver_name=$biggipserver_value"
    );

$result = $w->request( $url, $fields );

$html = str_get_html( $result );
// echo $result;
// Find all td tags with attribite align=center in table tags
$table = $html->find('table', -1);

foreach( $table->find('tr') as $tr )
{
    $td = $tr->find( 'td', 3 );

    $aa = $td;  // don't know why? fix me

    if( isset( $aa ) )
    {
        $em = $aa->find('ul', 0 );
        $employ_name = trim( substr( trim( $em->find( 'li', 0 )->plaintext ), 9 ) ); // 名字:
        $employ_id = trim( substr( trim( $em->find( 'li', 1 )->plaintext ), 9 ) ); // 工號:
        $employ_dep = trim( substr( trim( $em->find( 'li', 2 )->plaintext ), 9 ) ); // 部門:
        $employ_phone = trim( substr( trim( $em->find( 'li', 4 )->plaintext ), 3*5 ) ); // 分機號碼:
        $employ_org = trim( substr( trim( $em->find( 'li', 5 )->plaintext ), 6 ) ); // 分機號碼:

        $employ_info = $employ_id . "  " . $employ_name . " " . $employ_org . " - " . $employ_phone . " " . $employ_dep;
        // $employ_info = $employ_name;
        // print_r( $employ_info );
        if( !file_exists( "images/$employ_id.jpg" ) )
        {
            // download image
            $image_url = "http://10.128.0.10/engineers/images/$employ_id.jpg";
            $ch = curl_init( $image_url );
            $fp = fopen("images/$employ_id.jpg", 'wb');
            curl_setopt($ch, CURLOPT_FILE, $fp);
            curl_setopt($ch, CURLOPT_HEADER, 0);
            curl_exec($ch);
            curl_close($ch);
            fclose($fp);
        }
        $path = $w->path();
        // http://alfredworkflow.readthedocs.org/en/latest/xml_format.html#param-type
        $w->result( 'employ', "$path/images/$employ_id.jpg", $employ_info, '', "images/$employ_id.jpg", 'yes', $employ_name, 'file' );
    }
}

echo $w->toxml();
