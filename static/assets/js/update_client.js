$(document).ready(function() {
    // Function to handle changes in province dropdown
    $('#province').change(function () {
        $("#district").empty();
        var provinceId = $(this).val();
        $.ajax({
            url: getDistrictUrl, // Use the defined variable here
            data: { province_id: provinceId },
            success: function (data) {
                $("#district").append('<option value="" selected disabled hidden>อำเภอ/เขต</option>');
                $.each(data, function (index, value) {
                    $("#district").append('<option value="' + data[index].id + '">' + data[index].name_th + '</option>');
                });
            },
            error: function (xhr, status, error) {
                console.error('Error fetching districts:', error);
            }
        });
    });
    
    // Function to handle changes in district dropdown
    $('#district').change(function () {
        $('#subdistrict').empty();
        var districtId = $(this).val();
        $.ajax({
            url: getSubdistrictUrl, // Use the defined variable here
            data: { district_id: districtId },
            success: function (data) {
                $('#subdistrict').append('<option value="" selected disabled hidden>ตำบล/แขวง</option>');
                $.each(data, function (i, v) {
                    $('#subdistrict').append('<option value="' + data[i].id + '">' + data[i].name_th + '  ' + data[i].zipcode + '</option>');
                });
            },
            error: function (xhr, status, error) {
                console.error('Error fetching subdistricts:', error);
            }
        });
    });
});