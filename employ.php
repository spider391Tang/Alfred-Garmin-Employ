<?php
require_once('workflows.php');
require_once('simple_html_dom.php');

$w = new Workflows();

// Employ info from input
$query = trim($argv[1]);

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

if( is_numeric( $query ) )
{
    $fields = array
        ( 
            CURLOPT_POSTFIELDS => "WorkType=5&cboEmpID1=$query",
            CURLOPT_COOKIE => "$aspsession_name=$aspsession_value; $biggipserver_name=$biggipserver_value"
        );

    $result = $w->request( $url, $fields );
    preg_match('/分機號碼...([0-9]+)/', $result, $matches_phone);
    preg_match('/ORG...(.+?)<\/li>/', $result, $matches_org);
    preg_match('/部門...(.+?)\s+<li>/', $result, $matches_dep);
    $rtn = preg_match('/名字...<font color=blue>(.*?)<\/font>/', $result, $matches_name);

    $employ_info = $matches_name[1] . " " . $matches_org[1] . " - " . $matches_phone[1] . " " . $matches_dep[1];

    if( $rtn == 1 and !file_exists( "images/$query.jpg" ) )
    {
        // download image
        $image_url = "http://10.128.0.10/engineers/images/$query.jpg";
        $ch = curl_init( $image_url );
        $fp = fopen("images/$query.jpg", 'wb');
        curl_setopt($ch, CURLOPT_FILE, $fp);
        curl_setopt($ch, CURLOPT_HEADER, 0);
        curl_exec($ch);
        curl_close($ch);
        fclose($fp);
    }

    $w->result( 'employ', $query, $employ_info, '', "images/$query.jpg", 'yes', 'autocomplete' );
} 
else
{
    $fields = array
        ( 
            CURLOPT_POSTFIELDS => "WorkType=6&cboEmpName=$query",
            CURLOPT_COOKIE => "$aspsession_name=$aspsession_value; $biggipserver_name=$biggipserver_value"
        );
    $result = $w->request( $url, $fields );

    $html = str_get_html( $result );
    // echo $result;
    // Find all td tags with attribite align=center in table tags
    $table = $html->find('table', -1);
    // echo $table_str;

    // $table = str_get_html( $table_str );
    // $html->clear(); 
    // unset($html);

    // echo $table;
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
            $w->result( 'employ', $query, $employ_info, '', "images/$employ_id.jpg", 'yes', $employ_name );
        }
        // $em = $td->find('ul', 0 );

        // echo $em;
        // $employ_name = trim( substr( trim( $td->find( 'li', 0 )->plaintext ), 9 ) ); // 名字:
        // $employ_id = trim( substr( trim( $em->find( 'li', 1 )->plaintext ), 9 ) ); // 工號:
        // $employ_dep = trim( substr( trim( $em->find( 'li', 2 )->plaintext ), 9 ) ); // 部門:
        // $employ_phone = trim( substr( trim( $em->find( 'li', 4 )->plaintext ), 3*5 ) ); // 分機號碼:
        // $employ_org = trim( substr( trim( $em->find( 'li', 5 )->plaintext ), 6 ) ); // 分機號碼:
        // // print_r( $employ_dep );
        // // print_r( trim( $em->find( 'li', 5 )->plaintext ) );
        // // foreach( $employ->find( 'li' ) as $li )
        // // {
        // //     // $li_str = $li;
        // //     echo $li;
        // //     // print_r( $li_str );
        // // }
        // // $li = $employ->find('td ul');
        // // $em->clear();
        // unset( $em );
        // $td->clear();
        // unset( $td );
        // $tr->clear();
        // unset( $tr );
        // break;
    }

    // print_r( $es );
    // $rtn = preg_match('/名字...<font color=blue>(.*?)<\/font>/', $result, $matches_name);
}

echo $w->toxml();
