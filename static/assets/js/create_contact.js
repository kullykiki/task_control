$(function () {
    $('#province2').change(function () {
        $("#district2").empty();
        $.ajax({
            url: "{{ get_district_url }}",
            data: { province_id: $(this).val() },
            success: function (data) {
                $("#district2").append('<option value selected disabled hidden>อำเภอ/เขต</option>');
                $.each(data, function (index, value) {
                    $("#district2").append('<option value="' + data[index].id + '">' + data[index].name_th + '</option>');
                });
            }
        });
    });

    $('#district2').change(function () {
        $('#subdistrict2').empty();
        $.ajax({
            url: "{{ get_subdistrict_url }}",
            data: { district_id: $(this).val() },
            success: function (data) {
                $('#subdistrict2').append('<option value selected disabled hidden>ตำบล/แขวง/รหัสไปรษณีย์</option>');
                $.each(data, function (i, v) {
                    $('#subdistrict2').append('<option value="' + data[i].id + '">' + data[i].name_th + ' ' + data[i].zipcode + '</option>');
                });
            }
        });
    });
});

$(document).ready(function () {
    $("#createContactForm").on("submit", function (event) {
        event.preventDefault();
        var name = $("#ct_name").val();
        var position = $("#ct_position").val();
        var phone = $("#ct_phone").val();
        var email = $("#ct_email").val();
        var line = $("#ct_line").val();
        var other = $("#ct_other").val();
        var address = $("#ct_address").val();
        var address2 = $("#ct_address2").val();
        var province = $("#province2").val();
        var district = $("#district2").val();
        var subdistrict = $("#subdistrict2").val();
        var data = {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            name: name,
            position: position,
            phone: phone,
            email: email,
            line: line,
            other: other,
            address: address,
            address2: address2,
            province: province,
            district: district,
            subdistrict: subdistrict
        };
        $.ajax({
            type: 'POST',
            url: "{{ create_contact_url }}",
            data: data,
            success: function (response) {
                console.log(response);
                window.location.reload();
            },
            error: function (xhr, status, error) {
                console.error(xhr.responseText);
            }
        });
    });

    $('.delete-contact-btn').click(function() {
        if (confirm("Are you sure you want to delete this contact?")) {
            var contactId = $(this).data('contact-id');
            $.ajax({
                url: '{% url "taskcontrol:delete_contact" contact_id=0 %}'.replace('0', contactId),
                method: 'POST',
                headers: {'X-CSRFToken': '{{ csrf_token }}'},
                success: function(data) {
                    // Optionally handle success response
                    // For example, you can remove the contact row from the table
                    $('#contact-row-' + contactId).remove();
                    window.location.reload();
                },
                error: function(xhr, status, error) {
                    // Optionally handle error response
                }
            });
        }
    });
});