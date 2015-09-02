# coding: utf-8

"""Custom forms."""

from collections import OrderedDict

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib import parameters

from .models import ARmessage


class ARmessageForm(forms.ModelForm):

    """Form to define an auto-reply message."""

    fromdate = forms.DateTimeField(
        label=ugettext_lazy('From'),
        required=False,
        help_text=ugettext_lazy(
            "Activate your auto reply from this date. "
            "Format : YYYY-MM-DD HH:mm:ss"
        ),
        widget=forms.TextInput(
            attrs={'class': 'datefield form-control'}
        )
    )
    untildate = forms.DateTimeField(
        label=ugettext_lazy('Until'),
        required=False,
        help_text=ugettext_lazy(
            "Activate your auto reply until this date. "
            "Format : YYYY-MM-DD HH:mm:ss"
        ),
        widget=forms.TextInput(
            attrs={'class': 'datefield form-control'}
        )
    )
    subject = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={'class': 'form-control'}
        )
    )

    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled', 'fromdate', 'untildate')

    def __init__(self, *args, **kwargs):
        self.mailbox = args[0]
        super(ARmessageForm, self).__init__(*args[1:], **kwargs)
        self.fields = OrderedDict(
            (key, self.fields[key]) for key in
            ['subject', 'content', 'fromdate', 'untildate', 'enabled']
        )
        if not self.instance.pk:
            self.fields["subject"].initial = parameters.get_admin(
                "DEFAULT_SUBJECT")
            self.fields["content"].initial = parameters.get_admin(
                "DEFAULT_CONTENT")
        instance = kwargs.get("instance")
        if instance is not None:
            if instance.enabled:
                self.fields["fromdate"].initial = (
                    instance.fromdate.replace(second=0, microsecond=0)
                )
                self.fields["untildate"].initial = kwargs["instance"].untildate
            else:
                self.fields["fromdate"].initial = None

    def clean(self):
        """Custom fields validaton.

        We want to be sure that fromdate < untildate and that they are
        both in the future ONLY IF the autoreply is beeing activated.

        """
        cleaned_data = super(ARmessageForm, self).clean()
        if not cleaned_data.get("fromdate"):
            cleaned_data["fromdate"] = timezone.now()
        if not cleaned_data["enabled"]:
            return cleaned_data
        untildate = cleaned_data.get("untildate")
        if untildate is not None:
            if untildate < timezone.now():
                self.add_error("untildate", _("This date is over"))
            elif untildate < cleaned_data["fromdate"]:
                self.add_error(
                    "untildate", _("Must be greater than start date"))
        return cleaned_data

    def save(self, commit=True):
        """Custom save method."""
        instance = super(ARmessageForm, self).save(commit=False)
        instance.mbox = self.mailbox
        if commit:
            instance.save()
        return instance
