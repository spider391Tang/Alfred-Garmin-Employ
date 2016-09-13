<?php
require_once('workflows.php');
require_once('simple_html_dom.php');


// icons
$login_icon = "login.png";

// STATUS: ID, NAME, RANGE_ID
$status = "ID";


$w = new Workflows();

// Employ info from input
$query = trim( $argv[1] );

if( strlen( $query ) < 3 )
{
    exit;
}

// Leave office today
date_default_timezone_set('UTC');
const LEAVE_OFFICE_CACHE_LIFE = '600';
$leave_office_url = "http://prod.garmin.com.tw/PyrWeb2/attendance/qryindirectorytoday.asp";
$leave_office_file = "leave_office.html";
if ( !file_exists( $leave_office_file ) or ( time() - filectime( $leave_office_file ) >= LEAVE_OFFICE_CACHE_LIFE  ) )
{
    passthru("curl -d ORG_CODE=ALL --output $leave_office_file $leave_office_url");
}

$leave_office_html = file_get_html( $leave_office_file );

$leave_arr;
const LEAVE_ASK = 0;
const LEAVE_OUT = 1;
// 請假列表
$leave_hr = $leave_office_html->find( 'hr', 0 );

foreach( $leave_hr->find('table') as $t )
{
    foreach( $t->find('tr') as $tr )
    {
        $id = trim( $tr->find( 'td', 3 )->plaintext );
        $end_time = trim( $tr->find( 'td', 8 )->plaintext );
        if( is_numeric( $id ) and is_numeric( $end_time ) )
        {
            $start_date = substr( trim( $tr->find( 'td', 5 )->plaintext ), 4 );   // 20150608 => 0608
            $start_time = trim( $tr->find( 'td', 6 )->plaintext );
            $end_date = substr( trim( $tr->find( 'td', 7 )->plaintext ), 4 );
            if( strcmp( $start_date, $end_date ) == 0  )
            {
                $leave_arr[$id] = [ LEAVE_ASK, $start_time . "-" . $end_time ];
            }
            else
            {
                $leave_arr[$id] = [ LEAVE_ASK, $start_date . $start_time . "-" . $end_date . $end_time ];
            }
        }
    }
}

// 公出列表
$out_hr = $leave_office_html->find( 'hr', 1 );

foreach( $out_hr->find('table') as $t )
{
    foreach( $t->find('tr') as $tr )
    {
        $id = trim( $tr->find( 'td', 3 )->plaintext );
        $reason = trim( $tr->find( 'td', 9 )->plaintext );
        // echo $reason;
        if( is_numeric( $id ) )
        {
            $leave_arr[$id] = [ LEAVE_OUT, $reason ];
        }
    }
}

// Employee search
$url = "http://biz.garmin.com.tw/introduction/index.asp";

// Hack to access the 'Garmin Introduction' cookie
$host_name = "biz.garmin.com.tw";
$aspsession_prefix = "ASPSESSION";
$aspsession_name= "";
$aspsession_value= "";
$biggipserver_prefix = "BIGipServer";
$biggipserver_name = "";
$biggipserver_value = "";

$session_bak_json = file_get_contents('/Users/spider391tang/Library/Application Support/Firefox/Profiles/ixruv462.default-1465050097848/sessionstore-backups/recovery.js');
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

if( !$cookie_found )
{
    $w->result( 'employ', 'na', 'You should login first', 'Just press enter to login', $login_icon, 'yes' );
    echo $w->toxml();
    exit;
}

$query_fields = "";

if( is_numeric( $query ) )
{
    $status = "ID";
    $query_fields =  "WorkType=5&cboEmpID1=$query"; 
} 
else if( strpos( $query, '<' ) !== FALSE )
{
    $status = "RANGE_ID";
    $id = substr( $query, 0, -1 );
    $end_id = intval( $id ) + 50;
    $query_fields =  "WorkType=5&cboEmpID1=$id&cboEmpID2=$end_id"; 
}
else
{
    $status = "NAME";
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
        $employ_name = trim( preg_split("/[：:]+/", trim( $em->find( 'li', 0 )->plaintext ) )[1] ); // 名字:
        $employ_id = trim( preg_split("/[：:]+/", trim( $em->find( 'li', 1 )->plaintext ) )[1] ); // 工號:
        $employ_dep = trim( preg_split("/[：:]+/", trim( $em->find( 'li', 2 )->plaintext ) )[1] ); // 部門:
        $employ_phone = trim( preg_split("/[：:]+/", trim( $em->find( 'li', 4 )->plaintext ) )[1] ); // 分機號碼:
        $employ_org = trim( preg_split("/[：:]+/", trim( $em->find( 'li', 5 )->plaintext ) )[1] ); // 廠別:

        // echo trim( $em->find( 'li', 0 )->plaintext );

        // $employ_info = $employ_id . "" . $employ_name . "" . $employ_org . "-" . $employ_phone . "" . $employ_dep;
        $employ_info = $employ_name . "" . $employ_org . "-" . $employ_phone . " " . $employ_dep;
        if( !is_numeric( $query ) )
        {
            $employ_info = substr_replace( $employ_info, $employ_id, 0, 0 );
        }

        if( array_key_exists( $employ_id, $leave_arr ) )
        {
            $reason = "";
            if( $leave_arr[$employ_id][0] == LEAVE_ASK )
            {
                $reason = "請假";
            }
            else
            {
                $reason = "公出";
            }
            $employ_info = substr_replace( $employ_info, "(" . $reason . ":" . $leave_arr[$employ_id][1] . ")", 0, 0 );
        }

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
        // echo $employ_
        // http://alfredworkflow.readthedocs.org/en/latest/xml_format.html#param-type
        $w->result( 'employ', "$path/images/$employ_id.jpg", $employ_info, '', "images/$employ_id.jpg", 'no', $employ_name . 'EXT:' . $employ_phone, 'file' );
        // $w->result( 'employ', "$path/images/$employ_id.jpg", 'hello', '', "images/$employ_id.jpg", 'no', 'hello', 'file' );
    }
}

echo $w->toxml();
